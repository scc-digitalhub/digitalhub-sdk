# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import itertools
import os
import typing
from collections.abc import Mapping
from contextvars import ContextVar
from pathlib import Path
from threading import Lock
from types import MappingProxyType
from typing import NamedTuple

from digitalhub.entities._commons.enums import EntityTypes, Relationship
from digitalhub.factory.entity import entity_factory
from digitalhub.runtimes.enums import RuntimeEnvVar
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.stores.client.factory import resolve_client
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


# Run state local to the current execution context, for every Context, keyed by
# Context._state_key. One module-level variable instead of one per Context:
# contextvars.Context objects keep strong references to their variables, so
# per-instance variables accumulated as contexts were rebuilt. The mapping is
# replaced, never mutated, because copied execution contexts share it.
_LOCAL_RUN_STATE: ContextVar[Mapping[int, _RunContextState]] = ContextVar(
    "digitalhub_local_run_state",
    default=MappingProxyType({}),
)
_STATE_KEYS = itertools.count()


class Context:
    """
    Context class built from a Project instance.

    Contains project-specific information and state, including project name,
    client instance, local context paths, and run-time information.

    Attributes
    ----------
    name : str
        The name of the project.
    client : Client
        The client for the project's operations, resolved on every access
        unless one was assigned explicitly.
    config : dict
        Project configuration profile.
    root : Path
        The local context project path.
    is_running : bool
        Flag indicating if the context has an active run.
    run : Run | None
        Active Run in the current execution context, or the container run fallback.
    """

    # Explicitly assigned client; None means resolve on every access.
    _client_override: Client | None = None

    def __init__(self, project: Project) -> None:
        # Initialize context from project
        self.name: str = project.name
        self.config: dict = project.spec.config
        self._root: Path = Path(project.spec.source)

        self._run_ctx_searched = False
        self._run_ctx_lock = Lock()
        self._fallback_state = _RunContextState(None, False, {})
        # Per instance, not per project: a rebuilt context starts without local
        # state, and contexts with the same project name stay independent.
        self._state_key = next(_STATE_KEYS)

    @property
    def client(self) -> Client:
        """Return the assigned client, or resolve the project's client now."""
        if self._client_override is not None:
            return self._client_override
        return resolve_client(self.name)

    @client.setter
    def client(self, value: Client | None) -> None:
        """Pin a client to this context; ``None`` restores resolution on use."""
        self._client_override = value

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

    def _get_local_state(self) -> _RunContextState | None:
        return _LOCAL_RUN_STATE.get().get(self._state_key)

    def _set_local_state(self, state: _RunContextState | None) -> None:
        states = dict(_LOCAL_RUN_STATE.get())
        if state is None:
            states.pop(self._state_key, None)
        else:
            states[self._state_key] = state
        _LOCAL_RUN_STATE.set(MappingProxyType(states))

    def _get_run_context_state(self) -> _RunContextState:
        state = self._get_local_state()
        return state if state is not None else self._fallback_state

    def _set_run_context_state(self, state: _RunContextState) -> None:
        if self._get_local_state() is None:
            self._fallback_state = state
        else:
            self._set_local_state(state)

    def _resolve_run_ctx(self) -> None:
        if self._get_local_state() is None and not self._run_ctx_searched:
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
        self._set_local_state(_RunContextState(run, True, {}))

    def unset_run(self) -> None:
        """
        Clear the current run and reset running state and logged items.
        """
        self._mark_run_ctx_searched()
        state = self._get_local_state()
        if state is not None:
            state.logged.clear()
        self._set_local_state(None)

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
