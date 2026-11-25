# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
The session: the single owner of the SDK's runtime state.

The session owns the connection pool, the user identity, the project
contexts and the data stores. Clients and stores are views it builds for an
operation. Functions such as ``get_client()``, ``get_context()`` and
``get_store()`` reach it through ``get_session()``.
"""

from __future__ import annotations

import threading
import typing

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.client import Client
from digitalhub.stores.client.common.config import ClientConfig, get_client_config
from digitalhub.stores.client.http.transport import HttpTransport
from digitalhub.stores.data.builder import StoreBuilder

if typing.TYPE_CHECKING:
    from digitalhub.context.builder import ContextBuilder
    from digitalhub.stores.client.auth.provider import AuthProvider
    from digitalhub.stores.data._base.credentials import StoreCredentials
    from digitalhub.stores.data._base.store import Store


class Session:
    """
    Owner of the connection pool, user identity, contexts and stores.

    The SDK uses one per process, returned by ``get_session()``. ``transport``
    and ``identity`` can be given to build one for tests.

    Parameters
    ----------
    config : ClientConfig, optional
        Client configuration. Defaults to ``ClientConfig()``.
    transport : HttpTransport, optional
        Connection pool to use. Defaults to a new one owned by the session.
    identity : AuthProvider, optional
        User identity. Defaults to the profile and environment credentials,
        loaded on first use and reloaded after ``configure()``.
    """

    def __init__(
        self,
        config: ClientConfig | None = None,
        *,
        transport: HttpTransport | None = None,
        identity: AuthProvider | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._config = config if config is not None else ClientConfig()
        self._transport = transport if transport is not None else HttpTransport()
        self._given_identity = identity
        self._identity = identity
        self._user_client: Client | None = None
        self._contexts: ContextBuilder | None = None
        self._stores: StoreBuilder | None = None

    @property
    def config(self) -> ClientConfig:
        """The client configuration of this session."""
        return self._config

    def configure(self, config: ClientConfig) -> None:
        """
        Replace the client configuration.

        The next client is built with it and, unless one was given, the user
        identity is reloaded with it. The connection pool, contexts and
        stores are kept.
        """
        with self._lock:
            self._config = config
            self._user_client = None
            self._identity = self._given_identity

    def client(self, project: str | None = None) -> Client:
        """
        Return the client for an operation.

        Parameters
        ----------
        project : str, optional
            Project the operation targets. Every project currently uses the
            user identity; this is the hook for per-project credentials.

        Returns
        -------
        Client
            A client on the session's connection pool.
        """
        with self._lock:
            if self._user_client is None:
                if self._identity is None:
                    self._identity = ClientConfigurator(self._transport, self._config)
                self._user_client = Client(self._transport, self._identity, self._config)
            return self._user_client

    @property
    def contexts(self) -> ContextBuilder:
        """The project contexts of this session."""
        with self._lock:
            if self._contexts is None:
                # Imported here: the context layer resolves sessions, so it
                # cannot be imported while this module loads.
                from digitalhub.context.builder import ContextBuilder

                self._contexts = ContextBuilder()
            return self._contexts

    def store(self, uri: str, project: str | None = None) -> Store:
        """
        Return the store for a URI.

        Parameters
        ----------
        uri : str
            URI whose scheme selects the store.
        project : str, optional
            Project the data belongs to; see ``store_credentials()``.

        Returns
        -------
        Store
            The session's store for the URI scheme.
        """
        with self._lock:
            if self._stores is None:
                self._stores = StoreBuilder(self.store_credentials())
            stores = self._stores
        return stores.get(uri)

    def store_credentials(self, project: str | None = None) -> StoreCredentials:
        """
        Return the credentials stores connect with.

        Parameters
        ----------
        project : str, optional
            Project the data belongs to. Every project currently uses the
            user identity's credentials; this is the hook for per-project
            credentials.
        """
        return _UserStoreCredentials(self)


class _UserStoreCredentials:
    """Store credentials read from the session's user identity on every use."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self) -> dict:
        return self._session.client().get_credentials_and_config()

    def refresh(self) -> bool:
        return self._session.client().eval_retry(check_token_validity=True)


_session: Session | None = None
_session_lock = threading.Lock()


def get_session() -> Session:
    """
    Return the process session, creating it on first use.

    It uses the global client configuration; see ``set_client_config()``.
    """
    global _session
    session = _session
    if session is None:
        with _session_lock:
            if _session is None:
                _session = Session(get_client_config())
            session = _session
    return session


def configure_session(config: ClientConfig) -> None:
    """Apply a new client configuration to the session, if it exists."""
    with _session_lock:
        session = _session
    if session is not None:
        session.configure(config)
