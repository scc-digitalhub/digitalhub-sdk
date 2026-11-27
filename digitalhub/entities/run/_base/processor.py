# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes, State
from digitalhub.entities._commons.keys import EntityRef
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

if typing.TYPE_CHECKING:
    from digitalhub.entities.log._base.entity import Log
    from digitalhub.entities.run._base.entity import Run

logger = get_logger(__name__)

# States a local run goes through. Core keeps the state machine of the runs it
# executes, and takes the status of local runs as the SDK sends it: only the
# transitions the SDK makes are listed.
LOCAL_RUN_TRANSITIONS: dict[str, frozenset[str]] = {
    State.CREATED.value: frozenset({State.BUILT.value}),
    State.BUILT.value: frozenset({State.READY.value}),
    State.READY.value: frozenset({State.RUNNING.value}),
    State.RUNNING.value: frozenset({State.COMPLETED.value, State.ERROR.value}),
}


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
        if run.local_execution():
            self._check_transition(run, State.BUILT.value)
        runtime = runtime_factory.build_runtime(run.kind, run.project)
        spec = runtime.build(
            self.get_executable(run),
            self.get_task(run),
            run.to_dict(),
        )
        run.spec = run.spec.from_dict(spec)
        self._transition(run, State.BUILT)

    def run(self, run: Run) -> Run:
        """Execute the run state machine and persist the resulting status."""
        self.crud_processor.refresh_context_entity(run)
        self.start_execution(run)
        try:
            try:
                run._setup_execution()
                status = runtime_factory.build_runtime(run.kind, run.project).run(run.to_dict())
            except Exception as error:
                self.crud_processor.refresh_context_entity(run)
                run.status.message = str(error)
                if run.local_execution():
                    self._transition(run, State.ERROR)
                else:
                    self.crud_processor.update_context_entity(run)
                raise
        finally:
            self.end_execution(run)

        self.crud_processor.refresh_context_entity(run)
        if run.local_execution():
            self._check_transition(run, status.get("state"))
        else:
            status.pop("state", None)
        run.set_status({**run.status.to_dict(), **status})
        self.crud_processor.update_context_entity(run)
        return run

    def start_execution(self, run: Run) -> None:
        """Register the run as the active one and move a local run to READY, then RUNNING."""
        if run.local_execution():
            self._check_transition(run, State.READY.value)

        context = run._context()
        context.set_run(run)
        try:
            if run.local_execution():
                self._transition(run, State.READY)
                self._transition(run, State.RUNNING)
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
            self.crud_processor.refresh_context_entity(run)
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

    def _transition(self, run: Run, state: State) -> None:
        """Move ``run`` to ``state`` and save it; a local run must allow the transition."""
        if run.local_execution():
            self._check_transition(run, state.value)
        run.status.state = state.value
        self.crud_processor.update_context_entity(run)

    @staticmethod
    def _check_transition(run: Run, state: str | None) -> None:
        """Raise if a local run cannot go from its state to ``state``."""
        if state not in LOCAL_RUN_TRANSITIONS.get(run.status.state, frozenset()):
            raise EntityError(f"Local run {run.id} cannot go from {run.status.state} to {state}.")

    def get_executable(self, run: Run) -> dict:
        """Read the executable related to a run."""
        exec_kind = entity_factory.get_executable_kind(run.kind)
        entity_type = entity_factory.get_entity_type_from_kind(exec_kind)
        ref = EntityRef.parse(getattr(run.spec, entity_type))
        if ref.name is None:
            raise ValueError(f"Run executable reference for '{entity_type}' must contain a name and id.")
        return self.crud_processor.read_context_entity(
            ref.name,
            entity_type=entity_type,
            project=run.project,
            entity_id=ref.id,
        ).to_dict()

    def get_task(self, run: Run) -> dict:
        """Read the task related to a run."""
        return self.crud_processor.read_unversioned_entity(
            EntityRef.parse(run.spec.task).id,
            entity_type=EntityTypes.TASK.value,
            project=run.project,
        ).to_dict()
