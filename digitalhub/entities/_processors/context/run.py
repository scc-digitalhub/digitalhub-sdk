# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.uri_utils import parse_entity_reference

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.executable.protocol import ExecutableProtocol
    from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
    from digitalhub.entities.log._base.entity import Log
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task

logger = get_logger(__name__)


class ContextEntityRunProcessor:
    def __init__(
        self,
        crud_processor: ContextEntityCRUDProcessor | None = None,
        executable_processor: ContextEntityExecutableProcessor | None = None,
    ) -> None:
        self.crud_processor = crud_processor if crud_processor is not None else ContextEntityCRUDProcessor()
        self.executable_processor = executable_processor

    def execute_executable(
        self,
        executable: ExecutableProtocol,
        action: str,
        wait: bool = False,
        log_info: bool = True,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """Create and execute a run from an executable action."""
        if self.executable_processor is None:
            raise RuntimeError("Executable processor is not configured.")
        task = self.executable_processor.get_or_create_task(executable, action)
        run = self.executable_processor.create_run(
            executable,
            task,
            action,
            extensions=extensions,
            **kwargs,
        )
        return self.execute_run(run, wait=wait, log_info=log_info)

    def build_task_run(
        self,
        task: Task,
        run_kind: str,
        save: bool = True,
        **kwargs,
    ) -> Run:
        """Build a run from a task, optionally persisting it."""
        exec_kind = entity_factory.get_executable_kind(task.kind)
        exec_type = entity_factory.get_entity_type_from_kind(exec_kind)
        kwargs[exec_type] = getattr(task.spec, exec_type)
        return self.create_run(
            project=task.project,
            task=task._get_task_string(),
            kind=run_kind,
            entity_type=EntityTypes.RUN.value,
            save=save,
            **kwargs,
        )

    def create_run(self, save: bool = True, **kwargs) -> Run:
        """Create a run through persistence or entity construction."""
        if save:
            return self.crud_processor.create_context_entity(**kwargs)
        return entity_factory.build_entity_from_params(**kwargs)

    def get_run(self, entity_key: str) -> Run:
        """Read a run by ID or key."""
        return self.crud_processor.read_context_entity(entity_key)

    def delete_run(self, entity_key: str) -> dict:
        """Delete a run by ID or key."""
        return self.crud_processor.delete_context_entity(entity_key)

    def get_run_executable(self, run: Run) -> dict:
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

    def get_run_task(self, run: Run) -> dict:
        _, task_id = parse_entity_reference(run.spec.task)
        return self.crud_processor.read_unversioned_entity(
            task_id,
            entity_type="task",
            project=run.project,
        ).to_dict()

    def execute_run(self, run: Run, wait: bool = False, log_info: bool = True) -> Run:
        """Build and execute local runs, or wait for backend execution when requested."""
        if not run.local_execution():
            return run.wait(log_info=log_info) if wait else run

        run.build()
        return run.run()

    def read_run_logs(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        state: str | None = None,
    ) -> list[Log]:
        objects: list[dict] = get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.LOGS_READ,
                target=ContextEntityTarget(project, entity_type, entity_id),
                options=LogsOptions(state=state),
            )
        )
        logs = []
        for o in objects:
            content = o.pop("content", None)
            o["kind"] = EntityKinds.LOG_LOG.value
            entity: Log = entity_factory.build_entity_from_dict(o)
            entity.set_content(content)
            logs.append(entity)
        return logs
