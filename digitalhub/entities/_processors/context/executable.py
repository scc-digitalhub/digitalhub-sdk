# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes, Relationship
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.utils import (
    get_context,
    get_context_from_identifier,
    parse_identifier,
    update_entity_identity,
)
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.executable.protocol import ExecutableProtocol
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task
    from digitalhub.entities.trigger._base.entity import Trigger


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
            if getattr(task_obj.spec, executable.ENTITY_TYPE, None) != executable._get_executable_string():
                continue

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
        task: Task,
        action: str,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """Create and persist a run for an executable action."""
        run_kind = entity_factory.get_run_kind_from_action(executable.kind, action)
        run = task.run(run_kind, save=False, **kwargs)
        if extensions is not None:
            run.extensions.extend(extensions)
        run.add_relationship(Relationship.RUN_OF.value, executable.key)
        run.save()
        return run

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

        try:
            bck_obj = self.crud_processor._create_context_entity(ctx, obj.ENTITY_TYPE, obj.to_dict())
            new_obj: ExecutableProtocol = entity_factory.build_entity_from_dict(bck_obj, entity_type=entity_type)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")

        self.import_tasks(new_obj, tsk_dicts)
        return new_obj

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

        try:
            backend_obj = self.crud_processor._update_context_entity(context, obj.ENTITY_TYPE, obj.id, obj.to_dict())
        except EntityNotExistsError:
            backend_obj = self.crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())

        new_obj: ExecutableProtocol = entity_factory.build_entity_from_dict(backend_obj, entity_type=entity_type)
        self.import_tasks(new_obj, tsk_dicts)
        return new_obj
