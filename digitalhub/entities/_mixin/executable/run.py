# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.executable.base import ExecutableBaseMixin
from digitalhub.entities._processors.processors import executable_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class ExecutableRunMixin(ExecutableBaseMixin):
    def new_run(
        self,
        action: str,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """Create a persisted run for an executable action.

        Parameters
        ----------
        action : str
            Action implemented by the task.
        extensions : list[dict], optional
            Additional run extensions.
        **kwargs : dict
            Run construction parameters.

        Returns
        -------
        Run
            Created run.
        """
        return executable_processor.create_run(
            self,
            action,
            extensions=extensions,
            **kwargs,
        )

    def get_run(self, identifier: str) -> Run:
        """Get a run belonging to the executable.

        Parameters
        ----------
        identifier : str
            Run ID or key.

        Returns
        -------
        Run
            Matching run.

        Raises
        ------
        EntityError
            If the run does not exist or belongs to another executable.
        """
        return executable_processor.get_executable_run(self, identifier)

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
        """List runs associated with the executable.

        Parameters
        ----------
        q : str, optional
            Free-text query.
        name : str, optional
            Run name filter.
        kind : str, optional
            Run kind filter.
        user : str, optional
            Run owner filter.
        state : str, optional
            Run state filter.
        created : str, optional
            Creation date filter.
        updated : str, optional
            Update date filter.
        task : str, optional
            Task reference filter.
        action : str, optional
            Action filter.

        Returns
        -------
        list[Run]
            Runs matching the filters.
        """
        return executable_processor.list_executable_runs(
            self,
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

    def delete_run(self, identifier: str) -> dict:
        """Delete a run belonging to the executable.

        Parameters
        ----------
        identifier : str
            Run ID or key.

        Returns
        -------
        dict
            Backend deletion response.
        """
        return executable_processor.delete_executable_run(self, identifier)
