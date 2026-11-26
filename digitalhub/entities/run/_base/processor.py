# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes, State
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.factory.runtime import runtime_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.uri_utils import parse_entity_reference

if typing.TYPE_CHECKING:
    from digitalhub.entities.log._base.entity import Log
    from digitalhub.entities.run._base.entity import Run

logger = get_logger(__name__)


class RunProcessor:
    """Lifecycle of a run: build, execution, wait and logs."""

    def __init__(self, crud_processor: ContextEntityCRUDProcessor | None = None) -> None:
        self.crud_processor = ContextEntityCRUDProcessor() if crud_processor is None else crud_processor

    def execute(self, run: Run, wait: bool = False, log_info: bool = True) -> Run:
        """Build and execute local runs, or wait for backend execution when requested."""
        if not run.local_execution():
            return run.wait(log_info=log_info) if wait else run

        self.build(run)
        return self.run(run)

    def build(self, run: Run) -> None:
        """Build a run specification with its executable, task, and runtime."""
        runtime = runtime_factory.build_runtime(run.kind, run.project)
        spec = runtime.build(
            self.get_executable(run),
            self.get_task(run),
            run.to_dict(),
        )
        run.spec = run.spec.from_dict(spec)
        run.status.state = State.BUILT.value
        self._update(run)

    def run(self, run: Run) -> Run:
        """Execute the run state machine and persist the resulting status."""
        self._refresh(run)
        self.start_execution(run)
        try:
            run._setup_execution()
            try:
                status = runtime_factory.build_runtime(run.kind, run.project).run(run.to_dict())
            except Exception as error:
                self._refresh(run)
                if run.local_execution():
                    run.status.state = State.ERROR.value
                run.status.message = str(error)
                self._update(run)
                raise
        finally:
            self.end_execution(run)

        self._refresh(run)
        if not run.local_execution():
            status.pop("state", None)
        run.set_status({**run.status.to_dict(), **status})
        self._update(run)
        return run

    def start_execution(self, run: Run) -> None:
        """Register an active run and persist initial local execution state."""
        if run.local_execution() and run.status.state not in (State.BUILT.value, State.STOPPED.value):
            raise EntityError("Run is not in a state to run.")

        context = run._context()
        context.set_run(run)
        try:
            if run.local_execution():
                run.status.state = State.READY.value
                self._update(run)
                run.status.state = State.RUNNING.value
                self._update(run)
        except BaseException:
            context.unset_run()
            raise

    def end_execution(self, run: Run) -> None:
        """Unregister the active run from its context."""
        run._context().unset_run()

    def wait(
        self,
        run: Run,
        log_info: bool = True,
        timeout: float | None = None,
        poll_interval: float = 5.0,
    ) -> Run:
        """Wait until a run reaches a terminal state."""
        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be non-negative.")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive.")

        start = time.monotonic()
        terminal_states = {
            State.STOPPED.value,
            State.ERROR.value,
            State.COMPLETED.value,
        }
        while True:
            if log_info:
                logger.info(f"Waiting for run {run.id} to finish...")
            self._refresh(run)
            elapsed = time.monotonic() - start
            if run.status.state in terminal_states:
                if log_info:
                    logger.info(f"Run {run.id} finished in {elapsed:.2f} seconds.")
                return run
            if timeout is not None:
                remaining = timeout - elapsed
                if remaining <= 0:
                    raise TimeoutError(f"Run {run.id} did not finish within {timeout}s")
                time.sleep(min(poll_interval, remaining))
            else:
                time.sleep(poll_interval)

    def read_logs(
        self,
        run: Run,
        as_entity: bool = False,
        state: str | None = None,
    ) -> list[Log] | list[str]:
        """Read and build logs associated with a run."""
        objects: list[dict] = get_context(run.project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.LOGS_READ,
                target=ContextEntityTarget(run.project, run.ENTITY_TYPE, run.id),
                options=LogsOptions(state=state),
            )
        )
        logs = []
        for obj in objects:
            content = obj.pop("content", None)
            obj["kind"] = EntityKinds.LOG_LOG.value
            log: Log = entity_factory.build_entity_from_dict(obj)
            log.set_content(content)
            logs.append(log)
        if as_entity:
            return logs
        return [log.text for log in logs]

    def _update(self, run: Run) -> None:
        """Persist ``run`` and take back the backend state."""
        run._update_attributes(
            self.crud_processor.update_context_entity(run.project, run.ENTITY_TYPE, run.id, run.to_dict())
        )

    def _refresh(self, run: Run) -> None:
        """Replace the attributes of ``run`` with the backend state."""
        run._update_attributes(self.crud_processor.read_context_entity(run.key, entity_type=run.ENTITY_TYPE))

    def get_executable(self, run: Run) -> dict:
        """Read the executable related to a run."""
        exec_kind = entity_factory.get_executable_kind(run.kind)
        entity_type = entity_factory.get_entity_type_from_kind(exec_kind)
        entity_name, entity_id = parse_entity_reference(getattr(run.spec, entity_type))
        if entity_name is None:
            raise ValueError(f"Run executable reference for '{entity_type}' must contain a name and id.")
        return self.crud_processor.read_context_entity(
            entity_name,
            entity_type=entity_type,
            project=run.project,
            entity_id=entity_id,
        ).to_dict()

    def get_task(self, run: Run) -> dict:
        """Read the task related to a run."""
        _, task_id = parse_entity_reference(run.spec.task)
        return self.crud_processor.read_unversioned_entity(
            task_id,
            entity_type=EntityTypes.TASK.value,
            project=run.project,
        ).to_dict()
