# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import threading
import typing
from collections.abc import Callable, Mapping

from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.uri_utils import SchemeCategory, map_uri_scheme

if typing.TYPE_CHECKING:
    from digitalhub.stores.data._base.credentials import StoreCredentials
    from digitalhub.stores.data._base.store import Store

StoreFactory = Callable[["StoreCredentials"], "Store"]


def _build_hf_store(credentials: StoreCredentials) -> Store:
    from digitalhub.stores.data.hf.store import HFStore

    return HFStore()


def _build_local_store(credentials: StoreCredentials) -> Store:
    from digitalhub.stores.data.local.store import LocalStore

    return LocalStore()


def _build_remote_store(credentials: StoreCredentials) -> Store:
    from digitalhub.stores.data.remote.store import RemoteStore

    return RemoteStore()


def _build_s3_store(credentials: StoreCredentials) -> Store:
    from digitalhub.stores.data.s3.store import S3Store

    return S3Store(credentials)


def _build_sql_store(credentials: StoreCredentials) -> Store:
    from digitalhub.stores.data.sql.store import SqlStore

    return SqlStore(credentials)


DEFAULT_STORE_FACTORIES: Mapping[str, StoreFactory] = {
    SchemeCategory.S3.value: _build_s3_store,
    SchemeCategory.HF.value: _build_hf_store,
    SchemeCategory.SQL.value: _build_sql_store,
    SchemeCategory.LOCAL.value: _build_local_store,
    SchemeCategory.REMOTE.value: _build_remote_store,
}


class StoreBuilder:
    """
    Store factory and cache for one owner, usually a session.

    Stores are built on first use, one per store type, with the credentials
    given to the builder. Store modules are imported only when a store of
    that type is first needed.

    Parameters
    ----------
    credentials : StoreCredentials
        Credentials passed to the stores that need them.
    factories : Mapping[str, StoreFactory], optional
        Store factories by store type. Defaults to ``DEFAULT_STORE_FACTORIES``.
    """

    def __init__(
        self,
        credentials: StoreCredentials,
        factories: Mapping[str, StoreFactory] | None = None,
    ) -> None:
        self._credentials = credentials
        self._builders: dict[str, StoreFactory] = dict(DEFAULT_STORE_FACTORIES if factories is None else factories)
        self._instances: dict[str, Store] = {}
        self._lock = threading.Lock()

    def register(self, store_type: str, store: StoreFactory) -> None:
        """
        Register a store type with its factory.

        Parameters
        ----------
        store_type : str
            The unique identifier for the store type (e.g., 's3', 'sql').
        store : StoreFactory
            The factory used to create stores for this type.
        """
        with self._lock:
            if store_type in self._builders:
                raise StoreError(f"Store type {store_type} already registered")
            self._builders[store_type] = store

    def get(self, uri: str) -> Store:
        """
        Get or create the store for the URI scheme.

        Parameters
        ----------
        uri : str
            The URI whose scheme (e.g., 's3://', 'sql://') selects the store.

        Returns
        -------
        Store
            The store instance appropriate for handling the given URI.
        """
        store_type = map_uri_scheme(uri)
        with self._lock:
            store = self._instances.get(store_type)
            if store is None:
                store = self._builders[store_type](self._credentials)
                self._instances[store_type] = store
            return store
