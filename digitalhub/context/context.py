# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import typing
from pathlib import Path

from digitalhub.entities._commons.enums import EntityTypes, Relationship
from digitalhub.factory.entity import entity_factory
from digitalhub.runtimes.enums import RuntimeEnvVar
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
from digitalhub.utils.exceptions import BackendError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.project._base.entity import Project
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.stores.client.base.client import Client


class Context:
    """
    Context class built from a Project instance.

    Contains project-specific information and state, including project name,
    client instance, local context paths, and run-time information.

    Attributes
    ----------
    name : str
        The name of the project.
    client : BaseClient
        The client instance (local or remote) associated with the project.
    config : dict
        Project configuration profile.
    root : Path
        The local context project path.
    is_running : bool
        Flag indicating if the context has an active run.
    _run : Run
        Current Run instance, if any.
    """

    def __init__(self, project: Project) -> None:
        # Initialize context from project
        self.name: str = project.name
        self.client: Client = project._client
        self.config: dict = project.spec.config
        self.root: Path = Path(project.spec.source)
        self.root.mkdir(parents=True, exist_ok=True)

        # Initialize run context
        self.is_running: bool = False
        self.run: Run | None = None
        self.logged: dict[str, str] = {}
        self._search_run_ctx()

    def _search_run_ctx(self) -> None:
        """
        Search for an existing run id in env.
        """
        run_id = os.getenv(RuntimeEnvVar.RUN_ID.value)
        if run_id is not None:
            try:
                self.set_run(self._get_run(run_id))
            except BackendError:
                pass

    def set_run(self, run: Run) -> None:
        """
        Set the current run.

        Parameters
        ----------
        run : Run
            The run to set.
        """
        self.is_running = True
        self.run = run

    def unset_run(self) -> None:
        """
        Clear the current run and reset running state and logged items.
        """
        self.is_running = False
        self.run = None
        self.logged.clear()

    def register_entity(self, obj: ContextEntity) -> ContextEntity:
        """
        Add a logged item to the context. Sets the PRODUCEDBY
        relationship from the current run.

        Parameters
        ----------
        obj : ContextEntity
            The logged item to add.
        """
        id_ = self.run.key + ":" + self.run.id
        obj.add_relationship(Relationship.PRODUCEDBY.value, id_)
        self.logged[obj.name] = obj.key
        return obj

    def _get_run(self, run_id: str) -> Run:
        """
        Get the current Run instance.

        Parameters
        ----------
        run_id : str
            The run id.

        Returns
        -------
        Run
            The current Run instance.
        """
        api = self.client.build_api(
            category=ApiCategories.CONTEXT.value,
            operation=BackendOperations.READ.value,
            project=self.name,
            entity_type=EntityTypes.RUN.value,
            entity_id=run_id,
        )
        run_dict = self.client.read_object(api=api)
        return entity_factory.build_entity_from_dict(obj=run_dict)
