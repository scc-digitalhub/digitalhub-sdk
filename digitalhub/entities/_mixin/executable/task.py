# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.executable.base import ExecutableBaseMixin
from digitalhub.entities._processors.processors import crud_processor
from digitalhub.entities.task.crud import delete_task, list_tasks
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities.task._base.entity import Task

logger = get_logger(__name__)


class ExecutableTaskMixin(ExecutableBaseMixin):
    _tasks: dict[str, Task]

    def _task_store(self) -> dict[str, Task]:
        try:
            return self._tasks
        except AttributeError:
            self._tasks = {}
            return self._tasks

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
        """Import tasks and associate matching ones with the executable.

        Parameters
        ----------
        tasks : list[dict]
            Serialized tasks to import.
        """
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
        """Create and persist a task for an executable action.

        Parameters
        ----------
        action : str
            Action implemented by the task.
        **kwargs : dict
            Task construction parameters.

        Returns
        -------
        Task
            Created task.

        Raises
        ------
        EntityError
            If a task already exists for the action or the action is not supported.
        """
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
        """Get the task associated with an executable action.

        Parameters
        ----------
        action : str
            Action implemented by the task.

        Returns
        -------
        Task
            Associated task.

        Raises
        ------
        EntityError
            If no task exists for the action or the action is not supported.
        """
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
        """List tasks associated with the executable.

        Parameters
        ----------
        q : str, optional
            Free-text query.
        name : str, optional
            Task name filter.
        kind : str, optional
            Task kind filter.
        user : str, optional
            Task owner filter.
        state : str, optional
            Task state filter.
        created : str, optional
            Creation date filter.
        updated : str, optional
            Update date filter.

        Returns
        -------
        list[Task]
            Tasks matching the filters.
        """
        return self._list_tasks(
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
        """Update the task associated with an executable action.

        Parameters
        ----------
        action : str
            Action implemented by the task.
        **kwargs : dict
            Updated task construction parameters.

        Returns
        -------
        Task
            Updated task.

        Raises
        ------
        EntityError
            If no task exists for the action or the action is not supported.
        """
        existing_task = self.get_task(action)
        task_store = self._task_store()

        kwargs["project"] = self.project
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["uuid"] = existing_task.id

        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save(update=True)
        task_store[action] = task
        return task

    def delete_task(self, action: str, cascade: bool = True) -> dict:
        """Delete the task associated with an executable action.

        Parameters
        ----------
        action : str
            Action implemented by the task.
        cascade : bool, default=True
            Whether to delete dependent entities.

        Returns
        -------
        dict
            Backend deletion response.
        """
        task = self.get_task(action)
        task_store = self._task_store()
        resp = delete_task(task.key, cascade=cascade)
        task_store.pop(action, None)
        return resp

    def set_task(self, action: str, **kwargs) -> Task:
        """Create or replace the task associated with an executable action.

        Parameters
        ----------
        action : str
            Action implemented by the task.
        **kwargs : dict
            Task construction parameters.

        Returns
        -------
        Task
            Created or replaced task.

        Raises
        ------
        EntityError
            If the action is not supported.
        """
        try:
            existing_task = self.get_task(action)
        except EntityError:
            return self.new_task(action, **kwargs)

        task_store = self._task_store()

        kwargs["project"] = self.project
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)
        kwargs["uuid"] = existing_task.id

        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save(update=True)
        task_store[action] = task
        return task

    def _get_task_from_backend(self, kind: str) -> list[Task]:
        params = {self.ENTITY_TYPE: self._get_executable_string(), "kind": kind}
        return crud_processor.list_context_entities(self.project, EntityTypes.TASK.value, **params)

    def _check_task_in_backend(self, kind: str) -> bool:
        return bool(self._get_task_from_backend(kind))

    def _raise_if_exists(self, action: str) -> None:
        kind = entity_factory.get_task_kind_from_action(self.kind, action)
        if self._check_task_in_backend(kind):
            raise EntityError(f"Task '{action}' already exists.")

    def _raise_if_not_exists(self, action: str) -> None:
        kind = entity_factory.get_task_kind_from_action(self.kind, action)
        if not self._check_task_in_backend(kind):
            raise EntityError(f"Task '{action}' is not created.")
