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
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.exceptions import BackendError, ContextError
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.project._base.entity import Project
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.stores.client.client import Client

logger = get_logger(__name__)


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
        self._root: Path = Path(project.spec.source)

        self._run_ctx_searched = False
        self._is_running = False
        self._run: Run | None = None
        self.logged: dict[str, str] = {}

    @property
    def root(self) -> Path:
        """Return the local context root without creating it."""
        return self._root

    @root.setter
    def root(self, path: str | Path) -> None:
        self._root = Path(path)

    def ensure_root(self) -> Path:
        """Create and return the local context root."""
        self._root.mkdir(parents=True, exist_ok=True)
        return self._root

    @property
    def is_running(self) -> bool:
        self._resolve_run_ctx()
        return self._is_running

    @is_running.setter
    def is_running(self, value: bool) -> None:
        self._is_running = value
        self._run_ctx_searched = True

    @property
    def run(self) -> Run | None:
        self._resolve_run_ctx()
        return self._run

    @run.setter
    def run(self, value: Run | None) -> None:
        self._run = value
        self._run_ctx_searched = True

    def _resolve_run_ctx(self) -> None:
        if not self._run_ctx_searched and self._run is None:
            self._search_run_ctx()

    def _search_run_ctx(self) -> None:
        """
        Search for an existing run id in env.
        """
        self._run_ctx_searched = True
        run_id = os.getenv(RuntimeEnvVar.RUN_ID.value)
        if run_id is not None:
            try:
                self.set_run(self._get_run(run_id))
            except BackendError:
                logger.debug(
                    f"Run '{run_id}' set in environment but not found in backend",
                    exc_info=True,
                )

    def set_run(self, run: Run) -> None:
        """
        Set the current run.
        """
        self._run_ctx_searched = True
        self._is_running = True
        self._run = run

    def unset_run(self) -> None:
        """
        Clear the current run and reset running state and logged items.
        """
        self._run_ctx_searched = True
        self._is_running = False
        self._run = None
        self.logged.clear()

    def register_entity(self, obj: ContextEntity) -> ContextEntity:
        """
        Add a logged item to the context. Sets the PRODUCEDBY
        relationship from the current run.
        """
        if self.run is None:
            raise ContextError("Cannot register entity without an active run.")

        id_ = self.run.key + ":" + self.run.id
        obj.add_relationship(Relationship.PRODUCEDBY.value, id_)
        self.logged[obj.name] = obj.key
        return obj

    def _get_run(self, run_id: str) -> Run:
        """
        Get the current Run instance.
        """
        run_dict = self.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.READ,
                target=ContextEntityTarget(self.name, EntityTypes.RUN.value, run_id),
            )
        )
        return entity_factory.build_entity_from_dict(obj=run_dict, entity_type=EntityTypes.RUN.value)
