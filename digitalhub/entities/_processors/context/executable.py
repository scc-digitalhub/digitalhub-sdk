# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes, Relationship, State
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._mixin.source.entity import SourceEntityMixin
from digitalhub.entities._processors.utils import (
    get_context,
    get_context_from_identifier,
    parse_identifier,
    update_entity_identity,
)
from digitalhub.factory.entity import entity_factory
from digitalhub.factory.runtime import runtime_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.uri_utils import parse_entity_reference

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.executable.protocol import ExecutableProtocol
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
    from digitalhub.entities.log._base.entity import Log
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task
    from digitalhub.entities.trigger._base.entity import Trigger

logger = get_logger(__name__)


class ContextEntityExecutableProcessor:
    """Processor for executable entity and relationship operations."""

    def __init__(self, crud_processor: ContextEntityCRUDProcessor):
        self.crud_processor = crud_processor

    def list_tasks(self, executable: ExecutableProtocol, **kwargs) -> list:
        """List tasks related to an executable."""
        kwargs[executable.ENTITY_TYPE] = executable._get_executable_string()
        return self.crud_processor.list_context_entities(
            project=executable.project,
            entity_type=EntityTypes.TASK.value,
            **kwargs,
        )

    def get_task(self, executable: ExecutableProtocol, action: str):
        """Return the task for an executable action."""
        kind = entity_factory.get_task_kind_from_action(executable.kind, action)
        tasks = self.list_tasks(executable, kind=kind)
        if not tasks:
            raise EntityError(f"Task {kind} is not created")
        return tasks[0]

    def create_task(self, executable: ExecutableProtocol, action: str, **kwargs):
        """Create and persist the task for an executable action."""
        kind = entity_factory.get_task_kind_from_action(executable.kind, action)
        if self.list_tasks(executable, kind=kind):
            raise EntityError(f"Task '{action}' already exists.")

        kwargs["project"] = executable.project
        kwargs[executable.ENTITY_TYPE] = executable._get_executable_string()
        kwargs["kind"] = kind
        task = entity_factory.build_entity_from_params(**kwargs)
        try:
            task.save()
        except EntityAlreadyExistsError:
            raise EntityError(f"Task '{action}' already exists.") from None
        return task

    def get_or_create_task(self, executable: ExecutableProtocol, action: str, **kwargs):
        """Return an existing task or create it for the action."""
        try:
            return self.get_task(executable, action)
        except EntityError:
            return self.create_task(executable, action, **kwargs)

    def update_task(self, executable: ExecutableProtocol, action: str, **kwargs):
        """Replace the persisted task configuration for an action."""
        existing_task = self.get_task(executable, action)
        kwargs["project"] = executable.project
        kwargs["kind"] = entity_factory.get_task_kind_from_action(executable.kind, action)
        kwargs[executable.ENTITY_TYPE] = executable._get_executable_string()
        kwargs["uuid"] = existing_task.id
        task = entity_factory.build_entity_from_params(**kwargs)
        task.update()
        return task

    def delete_task(self, executable: ExecutableProtocol, action: str, cascade: bool = True) -> dict:
        """Delete the task configured for an action."""
        task = self.get_task(executable, action)
        return self.crud_processor.delete_context_entity(
            task.key,
            entity_type=EntityTypes.TASK.value,
            cascade=cascade,
            unversioned=True,
        )

    def set_task(self, executable: ExecutableProtocol, action: str, **kwargs):
        """Create or replace the task for an action."""
        try:
            self.get_task(executable, action)
        except EntityError:
            return self.create_task(executable, action, **kwargs)
        return self.update_task(executable, action, **kwargs)

    def import_tasks(self, executable: ExecutableProtocol, tasks: list[dict]) -> None:
        """Persist serialized tasks belonging to an executable."""
        for task in tasks:
            if not isinstance(task, dict):
                continue
            task_obj = entity_factory.build_entity_from_dict(task, entity_type=EntityTypes.TASK.value)
            try:
                task_obj.save()
            except EntityAlreadyExistsError:
                pass

    def list_executable_runs(
        self,
        executable: ExecutableProtocol,
        **kwargs,
    ) -> list:
        """List runs related to an executable."""
        kwargs[executable.ENTITY_TYPE] = executable._get_executable_string()
        return self.crud_processor.list_context_entities(
            project=executable.project,
            entity_type=EntityTypes.RUN.value,
            **kwargs,
        )

    def get_executable_run(
        self,
        executable: ExecutableProtocol,
        identifier: str,
    ):
        """Return a related run by ID or key."""
        for run in self.list_executable_runs(executable):
            if run.id == identifier or run.key == identifier:
                return run
        raise EntityError(f"Run '{identifier}' does not exist or does not belong to this executable.")

    def create_run(
        self,
        executable: ExecutableProtocol,
        action: str,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """Create and persist a run for an executable action."""
        task = self.get_or_create_task(executable, action)
        run_kind = entity_factory.get_run_kind_from_action(executable.kind, action)
        run = task.run(run_kind, save=False, **kwargs)
        if extensions is not None:
            run.extensions.extend(extensions)
        run.add_relationship(Relationship.RUN_OF.value, executable.key)
        run.save()
        return run

    def execute_executable(
        self,
        executable: ExecutableProtocol,
        action: str,
        wait: bool = False,
        log_info: bool = True,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """Create and execute a run for an executable action."""
        run = self.create_run(
            executable,
            action,
            extensions=extensions,
            **kwargs,
        )
        return self.execute_run(run, wait=wait, log_info=log_info)

    def execute_run(self, run: Run, wait: bool = False, log_info: bool = True) -> Run:
        """Build and execute local runs, or wait for backend execution when requested."""
        if not run.local_execution():
            return run.wait(log_info=log_info) if wait else run

        self.build_run(run)
        return self.run_run(run)

    def build_run(self, run: Run) -> None:
        """Build a run specification with its executable, task, and runtime."""
        runtime = runtime_factory.build_runtime(run.kind, run.project)
        spec = runtime.build(
            self.get_run_executable(run),
            self.get_run_task(run),
            run.to_dict(),
        )
        run.spec = run.spec.from_dict(spec)
        run.status.state = State.BUILT.value
        run.update()

    def run_run(self, run: Run) -> Run:
        """Execute the run state machine and persist the resulting status."""
        run.refresh()
        self.start_run_execution(run)
        try:
            run._setup_execution()
            try:
                status = runtime_factory.build_runtime(run.kind, run.project).run(run.to_dict())
            except Exception as error:
                run.refresh()
                if run.local_execution():
                    run.status.state = State.ERROR.value
                run.status.message = str(error)
                run.update()
                raise
        finally:
            self.end_run_execution(run)

        run.refresh()
        if not run.local_execution():
            status.pop("state", None)
        run.set_status({**run.status.to_dict(), **status})
        run.update()
        return run

    def start_run_execution(self, run: Run) -> None:
        """Register an active run and persist initial local execution state."""
        if run.local_execution() and run.status.state not in (State.BUILT.value, State.STOPPED.value):
            raise EntityError("Run is not in a state to run.")

        context = run._context()
        context.set_run(run)
        try:
            if run.local_execution():
                run.status.state = State.READY.value
                run.update()
                run.status.state = State.RUNNING.value
                run.update()
        except BaseException:
            context.unset_run()
            raise

    def end_run_execution(self, run: Run) -> None:
        """Unregister the active run from its context."""
        run._context().unset_run()

    def wait_run(
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
            run.refresh()
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

    def read_run_logs(
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
        params = {
            **kwargs,
            "project": task.project,
            "task": task._get_task_string(),
            "kind": run_kind,
            "entity_type": EntityTypes.RUN.value,
        }
        if save:
            return self.crud_processor.create_context_entity(**params)
        return entity_factory.build_entity_from_params(**params)

    def get_run_executable(self, run: Run) -> dict:
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

    def get_run_task(self, run: Run) -> dict:
        """Read the task related to a run."""
        _, task_id = parse_entity_reference(run.spec.task)
        return self.crud_processor.read_unversioned_entity(
            task_id,
            entity_type=EntityTypes.TASK.value,
            project=run.project,
        ).to_dict()

    def delete_executable_run(
        self,
        executable: ExecutableProtocol,
        identifier: str,
    ) -> dict:
        """Delete a run only when it belongs to the executable."""
        run = self.get_executable_run(executable, identifier)
        return self.crud_processor.delete_context_entity(
            run.key,
            entity_type=EntityTypes.RUN.value,
            unversioned=True,
        )

    def list_executable_triggers(
        self,
        executable: ExecutableProtocol,
        **kwargs,
    ) -> list:
        """List triggers related to an executable."""
        kwargs[executable.ENTITY_TYPE] = executable._get_executable_string()
        return self.crud_processor.list_context_entities(
            project=executable.project,
            entity_type=EntityTypes.TRIGGER.value,
            **kwargs,
        )

    def get_executable_trigger(
        self,
        executable: ExecutableProtocol,
        identifier: str,
    ):
        """Return a related trigger by ID or key."""
        for trigger in self.list_executable_triggers(executable):
            if trigger.id == identifier or trigger.key == identifier:
                return trigger
        raise EntityError(f"Trigger '{identifier}' does not exist or does not belong to this executable.")

    def create_trigger(
        self,
        executable: ExecutableProtocol,
        action: str,
        kind: str,
        name: str,
        template: dict | None = None,
        **kwargs,
    ) -> Trigger:
        """Create and persist a trigger for an executable action."""
        task = self.get_or_create_task(executable, action)
        task_string = task._get_task_string()
        executable_string = executable._get_executable_string()
        run_kind = entity_factory.get_run_kind_from_action(executable.kind, action)

        if template is None:
            template = {}
        if not isinstance(template, dict):
            raise EntityError("Template must be a dictionary")
        template = dict(template)
        template["task"] = task_string
        template[executable.ENTITY_TYPE] = executable_string

        trigger = entity_factory.build_entity_from_params(
            **kwargs,
            project=executable.project,
            kind=kind,
            name=name,
            **{
                executable.ENTITY_TYPE: executable_string,
                "task": task_string,
                "template": entity_factory.build_spec(run_kind, **template).to_dict(),
            },
        )
        trigger.save()
        return trigger

    def import_executable_entity(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ExecutableProtocol:
        if (file is None) == (key is None):
            raise ValueError("Provide key or file, not both or none.")

        if file is not None:
            dict_obj: dict | list[dict] = read_yaml(file)
        else:
            ctx = get_context_from_identifier(key)
            dict_obj: dict = self.crud_processor._read_context_entity(ctx, key)

        if isinstance(dict_obj, list):
            exec_dict = dict_obj[0]
            exec_dict["status"] = {}
            tsk_dicts = []
            for item in dict_obj[1:]:
                item["status"] = {}
                tsk_dicts.append(item)
        else:
            exec_dict = dict_obj
            exec_dict["status"] = {}
            tsk_dicts = []

        if context is None:
            context = exec_dict["project"]

        ctx = get_context(context)
        _, entity_type, _, _, _ = parse_identifier(exec_dict["key"])
        obj: ExecutableProtocol = entity_factory.build_entity_from_dict(exec_dict, entity_type=entity_type)

        update_entity_identity(obj, context, build_uuid() if reset_id else None)
        self._upload_local_source(obj)

        try:
            bck_obj = self.crud_processor._create_context_entity(ctx, obj.ENTITY_TYPE, obj.to_dict())
            new_obj: ExecutableProtocol = entity_factory.build_entity_from_dict(bck_obj, entity_type=entity_type)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")

        self.import_tasks(new_obj, tsk_dicts)
        return new_obj

    @staticmethod
    def _upload_local_source(obj: ExecutableProtocol) -> None:
        """
        Upload or inline a local source read from a file, before saving.

        Done here and not in ``from_dict()``: deserialization stays free of
        I/O, and the upload goes to the project the entity is saved into.
        """
        if isinstance(obj, SourceEntityMixin):
            obj._post_build_source_check()

    def load_executable_entity(
        self,
        file: str,
    ) -> ExecutableProtocol:
        dict_obj: dict | list[dict] = read_yaml(file)
        if isinstance(dict_obj, list):
            exec_dict = dict_obj[0]
            tsk_dicts = dict_obj[1:]
        else:
            exec_dict = dict_obj
            tsk_dicts = []

        context = get_context(exec_dict["project"])
        _, entity_type, _, _, _ = parse_identifier(exec_dict["key"])
        obj: ExecutableProtocol = entity_factory.build_entity_from_dict(exec_dict, entity_type=entity_type)
        self._upload_local_source(obj)

        try:
            backend_obj = self.crud_processor._update_context_entity(context, obj.ENTITY_TYPE, obj.id, obj.to_dict())
        except EntityNotExistsError:
            backend_obj = self.crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())

        new_obj: ExecutableProtocol = entity_factory.build_entity_from_dict(backend_obj, entity_type=entity_type)
        self.import_tasks(new_obj, tsk_dicts)
        return new_obj
