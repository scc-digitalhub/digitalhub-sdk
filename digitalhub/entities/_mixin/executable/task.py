# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.executable.base import ExecutableBaseMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities.task._base.entity import Task


class ExecutableTaskMixin(ExecutableBaseMixin):
    def _get_or_create_task(self, action: str) -> Task:
        return ContextEntityExecutableProcessor().get_or_create_task(self, action)

    def import_tasks(self, tasks: list[dict]) -> None:
        """Create serialized tasks for the executable, in its project and pointing to it.

        Parameters
        ----------
        tasks : list[dict]
            Serialized tasks to import.
        """
        ContextEntityExecutableProcessor().import_tasks(self, tasks)

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
        return ContextEntityExecutableProcessor().create_task(self, action, **kwargs)

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
        return ContextEntityExecutableProcessor().get_task(self, action)

    def list_tasks(
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
        return ContextEntityExecutableProcessor().list_tasks(
            self,
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
        )

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
        return ContextEntityExecutableProcessor().update_task(self, action, **kwargs)

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
        return ContextEntityExecutableProcessor().delete_task(self, action, cascade=cascade)

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
        return ContextEntityExecutableProcessor().set_task(self, action, **kwargs)
