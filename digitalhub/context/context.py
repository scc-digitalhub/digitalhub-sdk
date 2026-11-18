# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import typing
from contextvars import ContextVar
from pathlib import Path
from threading import Lock
from typing import NamedTuple

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


class _RunContextState(NamedTuple):
    run: Run | None
    is_running: bool
    logged: dict[str, str]


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
    run : Run | None
        Active Run in the current execution context, or the container run fallback.
    """

    def __init__(self, project: Project) -> None:
        # Initialize context from project
        self.name: str = project.name
        self.client: Client = project._client
        self.config: dict = project.spec.config
        self._root: Path = Path(project.spec.source)

        self._run_ctx_searched = False
        self._run_ctx_lock = Lock()
        self._fallback_state = _RunContextState(None, False, {})
        context_name = f"digitalhub_run_context_{self.name}_{id(self)}"
        self._run_context: ContextVar[_RunContextState | None] = ContextVar(context_name, default=None)

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
        return self._get_run_context_state().is_running

    @is_running.setter
    def is_running(self, value: bool) -> None:
        self._mark_run_ctx_searched()
        self._set_run_context_state(self._get_run_context_state()._replace(is_running=value))

    @property
    def run(self) -> Run | None:
        self._resolve_run_ctx()
        return self._get_run_context_state().run

    @run.setter
    def run(self, value: Run | None) -> None:
        self._mark_run_ctx_searched()
        self._set_run_context_state(self._get_run_context_state()._replace(run=value))

    @property
    def logged(self) -> dict[str, str]:
        return self._get_run_context_state().logged

    @logged.setter
    def logged(self, value: dict[str, str]) -> None:
        self._set_run_context_state(self._get_run_context_state()._replace(logged=value))

    def _get_run_context_state(self) -> _RunContextState:
        state = self._run_context.get()
        return state if state is not None else self._fallback_state

    def _set_run_context_state(self, state: _RunContextState) -> None:
        if self._run_context.get() is None:
            self._fallback_state = state
        else:
            self._run_context.set(state)

    def _resolve_run_ctx(self) -> None:
        if self._run_context.get() is None and not self._run_ctx_searched:
            self._search_run_ctx()

    def _mark_run_ctx_searched(self) -> None:
        with self._run_ctx_lock:
            self._run_ctx_searched = True

    def _search_run_ctx(self) -> None:
        """
        Search for an existing run id in env.
        """
        with self._run_ctx_lock:
            if self._run_ctx_searched:
                return

            self._run_ctx_searched = True
            run_id = os.getenv(RuntimeEnvVar.RUN_ID.value)
            if run_id is not None:
                try:
                    self._fallback_state = self._fallback_state._replace(
                        run=self._get_run(run_id),
                        is_running=True,
                    )
                except BackendError:
                    logger.debug(
                        f"Run '{run_id}' set in environment but not found in backend",
                        exc_info=True,
                    )

    def set_run(self, run: Run) -> None:
        """
        Set the current run.
        """
        self._mark_run_ctx_searched()
        state = _RunContextState(run, True, {})
        self._run_context.set(state)

    def unset_run(self) -> None:
        """
        Clear the current run and reset running state and logged items.
        """
        self._mark_run_ctx_searched()
        state = self._run_context.get()
        if state is not None:
            state.logged.clear()
        self._fallback_state.logged.clear()
        self._run_context.set(None)

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
