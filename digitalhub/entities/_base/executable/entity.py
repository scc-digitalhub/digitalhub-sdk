# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor
from digitalhub.entities.run.crud import list_runs
from digitalhub.entities.task.crud import delete_task, list_tasks
from digitalhub.entities.trigger.crud import list_triggers
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.entity.spec import Spec, SpecValidator
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task
    from digitalhub.entities.trigger._base.entity import Trigger


class ExecutableEntity(VersionedEntity):
    """
    A class representing an entity that can be executed.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: Spec,
        status: Status,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        # Initialize tasks
        self._tasks: dict[str, Task] = {}

    ##############################
    #  Helpers
    ##############################

    def _get_executable_string(self) -> str:
        """
        Get executable string.

        Returns
        -------
        str
            Executable string.
        """
        return f"{self.kind}://{self.project}/{self.name}:{self.id}"

    ##############################
    #  Tasks
    ##############################

    def _get_or_create_task(self, action: str) -> Task:
        """
        Get or create task.

        Parameters
        ----------
        action : str
            Action name.

        Returns
        -------
        Task
            Task.
        """
        if self._tasks.get(action) is None:
            try:
                self._tasks[action] = self.get_task(action)
            except EntityError:
                self._tasks[action] = self.new_task(action)
        return self._tasks[action]

    def import_tasks(self, tasks: list[dict]) -> None:
        """
        Import tasks from yaml.

        Parameters
        ----------
        tasks : list[dict]
            List of tasks to import.
        """
        # Loop over tasks list, in the case where the function
        # is imported from local file.
        for task in tasks:
            # If task is not a dictionary, skip it
            if not isinstance(task, dict):
                continue

            # Create a new object from dictionary.
            # the form in which tasks are stored in function
            # status
            task_obj: Task = entity_factory.build_entity_from_dict(task)

            # Try to save it in backend to been able to use
            # it for launching runs. In fact, tasks must be
            # persisted in backend to be able to launch runs.
            # Ignore if task already exists
            try:
                task_obj.save()
            except EntityAlreadyExistsError:
                pass

            # Set task if function is the same. Overwrite
            # status task dict with the new task object
            if task_obj.spec.function == self._get_executable_string():
                action = entity_factory.get_action_from_task_kind(self.kind, task_obj.kind)
                self._tasks[action] = task_obj

    def new_task(self, action: str, **kwargs) -> Task:
        """
        Create new task. If the task already exists, update it.

        Parameters
        ----------
        action : str
            Action name.
        **kwargs : dict
            Task spec keyword arguments.

        Returns
        -------
        Task
            New task.
        """
        self._raise_if_exists(action)

        # Override kwargs
        kwargs["project"] = self.project
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)

        # Create object instance
        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save()

        self._tasks[action] = task
        return task

    def get_task(self, action: str) -> Task:
        """
        Get task.

        Parameters
        ----------
        action : str
            Action name.

        Returns
        -------
        Task
            Task.
        """
        try:
            return self._tasks[action]
        except KeyError:
            kind = entity_factory.get_task_kind_from_action(self.kind, action)
            resp = self._get_task_from_backend(kind)
            if not resp:
                raise EntityError(f"Task {kind} is not created")
            self._tasks[action] = resp[0]
            return self._tasks[action]

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
        """
        List tasks of the executable entity from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.

        Returns
        -------
        list[Task]
            List of object instances.
        """
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
        """
        List all tasks of the executable entity from backend.

        Returns
        -------
        list[Task]
            List of object instances.
        """
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_tasks(self.project, **kwargs)

    def update_task(self, action: str, **kwargs) -> Task:
        """
        Update task.

        Parameters
        ----------
        action : str
            Action name.
        **kwargs : dict
            Task spec keyword arguments.

        Returns
        -------
        Task
            Task.
        """
        self._raise_if_not_exists(action)

        # Update kwargs
        kwargs["project"] = self.project
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["uuid"] = self._tasks[action].id

        # Update task
        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save(update=True)
        self._tasks[action] = task
        return task

    def delete_task(self, action: str, cascade: bool = True) -> dict:
        """
        Delete task.

        Parameters
        ----------
        action : str
            Action name.
        cascade : bool
            Flag to determine if cascade deletion must be performed.

        Returns
        -------
        dict
            Response from backend.
        """
        resp = delete_task(self._tasks[action].key, cascade=cascade)
        self._tasks.pop(action, None)
        return resp

    def set_task(self, action: str, **kwargs) -> Task:
        """
        Set task.

        Parameters
        ----------
        action : str
            Action name.
        **kwargs : dict
            Task spec keyword arguments.

        Returns
        -------
        Task
            Task.
        """
        if self._tasks.get(action) is None:
            self.new_task(action, **kwargs)
            return self._tasks[action]

        # Override kwargs
        kwargs["project"] = self.project
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        kwargs["kind"] = entity_factory.get_task_kind_from_action(self.kind, action)

        # Create object instance
        task: Task = entity_factory.build_entity_from_params(**kwargs)
        task.save(update=True)
        self._tasks[action] = task
        return task

    def _get_task_from_backend(self, kind: str) -> list:
        """
        List tasks from backend filtered by function and kind.

        Parameters
        ----------
        kind : str
            Kind the object.

        Returns
        -------
        list
            Response from backend.
        """
        params = {self.ENTITY_TYPE: self._get_executable_string(), "kind": kind}
        return context_processor.list_context_entities(self.project, EntityTypes.TASK.value, **params)

    def _check_task_in_backend(self, kind: str) -> bool:
        """
        Check if task exists in backend.

        Parameters
        ----------
        kind : str
            Kind the object.

        Returns
        -------
        bool
            Flag to determine if task exists in backend.
        """
        resp = self._get_task_from_backend(kind)
        if not resp:
            return False
        return True

    def _raise_if_exists(self, action: str) -> None:
        """
        Raise error if task is created.

        Parameters
        ----------
        action : str
            Action name.

        Raises
        ------
        EntityError
            If task already exists.
        """
        if self._check_task_in_backend(action):
            raise EntityError(f"Task '{action}' already exists.")

    def _raise_if_not_exists(self, action: str) -> None:
        """
        Raise error if task is not created.

        Parameters
        ----------
        action : str
            Action name.

        Raises
        ------
        EntityError
            If task does not exist.
        """
        if self._tasks.get(action) is None:
            raise EntityError(f"Task '{action}' does not exist.")

    ##############################
    #  Runs
    ##############################

    @abstractmethod
    def run(self, *args, **kwargs) -> Run:
        """
        Create and execute a new run.
        """

    def get_run(self, identifier: str) -> Run:
        """
        Get specific run object of the executable from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity ID.

        Returns
        -------
        Run
            Object instance.
        """
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
        """
        List runs of the executable entity from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        state : str
            Object state.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        task : str
            Task string filter.
        action : str
            Action name filter.

        Returns
        -------
        list[Run]
            List of object instances.
        """
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
        """
        List all runs of the executable entity from backend.

        Returns
        -------
        list[Run]
            List of object instances.
        """
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_runs(self.project, **kwargs)

    ##############################
    #  Trigger
    ##############################

    def trigger(
        self,
        action: str,
        kind: str,
        name: str,
        template: dict | None = None,
        **kwargs,
    ) -> Trigger:
        """
        Trigger function.

        Parameters
        ----------
        action : str
            Action to execute.
        kind : str
            Trigger kind.
        name : str
            Trigger name.
        template : dict
            Template for the trigger.
        **kwargs : dict
            Keyword arguments passed to trigger builder.

        Returns
        -------
        Trigger
            Object instance.
        """
        # Get task
        task = self._get_or_create_task(action)
        task_string = task._get_task_string()
        exec_string = self._get_executable_string()

        # Get run validator for building trigger template
        run_kind = entity_factory.get_run_kind_from_action(self.kind, action)
        run_validator: SpecValidator = entity_factory.get_spec_validator(run_kind)

        # Override kwargs
        kwargs["project"] = self.project
        kwargs["kind"] = kind
        kwargs["name"] = name

        # Template handling
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

        # Create object instance
        trigger: Trigger = entity_factory.build_entity_from_params(**kwargs)
        trigger.save()
        return trigger

    def get_trigger(self, identifier: str) -> Trigger:
        """
        Get object from backend.

        Parameters
        ----------
        identifier : str
            Entity key (store://...) or entity ID.

        Returns
        -------
        Trigger
            Object instance.
        """
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
        """
        List triggers of the executable entity from backend.

        Parameters
        ----------
        q : str
            Query string to filter objects.
        name : str
            Object name.
        kind : str
            Kind of the object.
        user : str
            User that created the object.
        created : str
            Creation date filter.
        updated : str
            Update date filter.
        versions : str
            Object version, default is latest.
        task : str
            Task string filter.

        Returns
        -------
        list[Trigger]
            List of object instances.
        """
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
        """
        List triggers of the executable from backend.

        Parameters
        ----------
        **kwargs : dict
            Parameters to pass to the API call.

        Returns
        -------
        list[Trigger]
            List of object instances.
        """
        kwargs[self.ENTITY_TYPE] = self._get_executable_string()
        return list_triggers(self.project, **kwargs)
