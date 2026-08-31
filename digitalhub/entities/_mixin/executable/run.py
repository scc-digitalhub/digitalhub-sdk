# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.executable.base import ExecutableBaseMixin
from digitalhub.entities.run.crud import list_runs
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class ExecutableRunMixin(ExecutableBaseMixin):
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
