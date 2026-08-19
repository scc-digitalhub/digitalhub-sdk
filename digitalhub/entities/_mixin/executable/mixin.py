# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod
from typing import ClassVar

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import crud_processor
from digitalhub.entities.run.crud import list_runs
from digitalhub.entities.task.crud import delete_task, list_tasks
from digitalhub.entities.trigger.crud import list_triggers
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import SpecValidator
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task
    from digitalhub.entities.trigger._base.entity import Trigger

logger = get_logger(__name__)


class ExecutableMixin:
    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str
    _tasks: dict[str, Task]

    def _task_store(self) -> dict[str, Task]:
        try:
            return self._tasks
        except AttributeError:
            self._tasks = {}
            return self._tasks

    def _get_executable_string(self) -> str:
        return f"{self.kind}://{self.project}/{self.name}:{self.id}"

    def _get_or_create_task(self, action: str) -> Task:
        tasks = self._task_store()
        if tasks.get(action) is None:
            try:
                tasks[action] = self.get_task(action)
                logger.debug(f"Loaded existing task for action '{action}'.")
            except EntityError:
                logger.debug(f"Task for action '{action}' not found, creating new one.")
                tasks[action] = self.new_task(action)
        return tasks[action]

    def import_tasks(self, tasks: list[dict]) -> None:
        task_store = self._task_store()
        for task in tasks:
            if not isinstance(task, dict):
                continue

            task_obj: Task = entity_factory.build_entity_from_dict(task)

            try:
                task_obj.save()
            except EntityAlreadyExistsError:
                logger.debug(
                    f"Task '{task_obj.kind}' already exists in backend, skipping save.",
                )

            if task_obj.spec.function == self._get_executable_string():
                action = entity_factory.get_action_from_task_kind(self.kind, task_obj.kind)
                task_store[action] = task_obj

    def new_task(self, action: str, **kwargs) -> Task:
        self._raise_if_exists(action)
        task_store = self._task_store()

        kwargs["project"] = self.project
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)

        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save()

        task_store[action] = task
        return task

    def get_task(self, action: str) -> Task:
        task_store = self._task_store()
        try:
            return task_store[action]
        except KeyError:
            kind = entity_factory.get_task_kind_from_action(self.kind, action)
            resp = self._get_task_from_backend(kind)
            if not resp:
                raise EntityError(f"Task {kind} is not created")
            task_store[action] = resp[0]
            return task_store[action]

    def list_task(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
    ) -> list[Task]:
        return self._list_tasks(
            self.project,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
        )

    def _list_tasks(self, **kwargs) -> list[Task]:
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_tasks(self.project, **kwargs)

    def update_task(self, action: str, **kwargs) -> Task:
        self._raise_if_not_exists(action)
        task_store = self._task_store()

        kwargs["project"] = self.project
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["uuid"] = task_store[action].id

        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save(update=True)
        task_store[action] = task
        return task

    def delete_task(self, action: str, cascade: bool = True) -> dict:
        task_store = self._task_store()
        resp = delete_task(task_store[action].key, cascade=cascade)
        task_store.pop(action, None)
        return resp

    def set_task(self, action: str, **kwargs) -> Task:
        task_store = self._task_store()
        if task_store.get(action) is None:
            self.new_task(action, **kwargs)
            return task_store[action]

        kwargs["project"] = self.project
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)

        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save(update=True)
        task_store[action] = task
        return task

    def _get_task_from_backend(self, kind: str) -> list:
        params = {self.ENTITY_TYPE: self._get_executable_string(), "kind": kind}
        return crud_processor.list_context_entities(self.project, EntityTypes.TASK.value, **params)

    def _check_task_in_backend(self, kind: str) -> bool:
        return bool(self._get_task_from_backend(kind))

    def _raise_if_exists(self, action: str) -> None:
        if self._check_task_in_backend(action):
            raise EntityError(f"Task '{action}' already exists.")

    def _raise_if_not_exists(self, action: str) -> None:
        if not self._check_task_in_backend(action):
            raise EntityError(f"Task '{action}' is not created.")

    @abstractmethod
    def run(self, *args, **kwargs) -> Run:
        raise NotImplementedError

    def get_run(self, identifier: str) -> Run:
        entities = self._list_runs()
        for entity in entities:
            if getattr(entity.spec, self.ENTITY_TYPE) == self._get_executable_string():
                if entity.id == identifier:
                    return entity
                if entity.key == identifier:
                    return entity
        raise EntityError(f"Run '{identifier}' does not exist or does not belong to this executable.")

    def list_runs(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        task: str | None = None,
        action: str | None = None,
    ) -> list[Run]:
        return self._list_runs(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            task=task,
            action=action,
        )

    def _list_runs(self, **kwargs) -> list[Run]:
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_runs(self.project, **kwargs)

    def trigger(
        self,
        action: str,
        kind: str,
        name: str,
        template: dict | None = None,
        **kwargs,
    ) -> Trigger:
        task = self._get_or_create_task(action)
        task_string = task._get_task_string()
        exec_string = self._get_executable_string()

        run_kind = entity_factory.get_run_kind_from_action(self.kind, action)
        run_validator: SpecValidator = entity_factory.get_spec_validator(run_kind)

        kwargs["project"] = self.project
        kwargs["kind"] = kind
        kwargs["name"] = name

        if template is None:
            template = {}
        if not isinstance(template, dict):
            raise EntityError("Template must be a dictionary")

        template["task"] = task_string
        template[self.ENTITY_TYPE] = exec_string
        template = run_validator(**template).to_dict()

        kwargs[self.ENTITY_TYPE] = exec_string
        kwargs["task"] = task_string
        kwargs["template"] = template

        trigger: Trigger = entity_factory.build_entity_from_params(**kwargs)
        trigger.save()
        return trigger

    def get_trigger(self, identifier: str) -> Trigger:
        entities = self._list_triggers()
        for entity in entities:
            if getattr(entity.spec, self.ENTITY_TYPE) == self._get_executable_string():
                if entity.id == identifier:
                    return entity
                if entity.key == identifier:
                    return entity
        raise EntityError(f"Trigger '{identifier}' does not exist or does not belong to this executable.")

    def list_triggers(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
        task: str | None = None,
    ) -> list[Trigger]:
        return self._list_triggers(
            q=q,
            name=name,
            kind=kind,
            user=user,
            created=created,
            updated=updated,
            versions=versions,
            task=task,
        )

    def _list_triggers(self, **kwargs) -> list[Trigger]:
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_triggers(self.project, **kwargs)
