# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Callable

from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.uri_utils import SchemeCategory, map_uri_scheme

if typing.TYPE_CHECKING:
    from digitalhub.stores.data._base.store import Store


def _build_hf_store() -> Store:
    from digitalhub.stores.data.hf.store import HFStore

    return HFStore()


def _build_local_store() -> Store:
    from digitalhub.stores.data.local.store import LocalStore

    return LocalStore()


def _build_remote_store() -> Store:
    from digitalhub.stores.data.remote.store import RemoteStore

    return RemoteStore()


def _build_s3_store() -> Store:
    from digitalhub.stores.data.s3.store import S3Store

    return S3Store()


def _build_sql_store() -> Store:
    from digitalhub.stores.data.sql.store import SqlStore

    return SqlStore()


class StoreBuilder:
    """
    Store factory and registry for managing data store instances.

    Provides registration, instantiation, and caching of data store
    instances based on URI schemes. Supports various store types
    including S3, SQL, local, and remote stores with their respective
    configurators.

    Attributes
    ----------
    _builders : dict[str, StoreInfo]
        Registry of store types mapped to their StoreInfo instances.
    _instances : dict[str, Store]
        Cache of instantiated store instances by store type.
    """

    def __init__(self) -> None:
        self._builders: dict[str, Callable[[], Store]] = {}
        self._instances: dict[str, dict[str, Store]] = {}

    def register(
        self,
        store_type: str,
        store: Callable[[], Store],
    ) -> None:
        """
        Register a store type with its factory.

        Adds a new store type to the builder registry, associating it
        with a store class and optional configurator for later instantiation.

        Parameters
        ----------
        store_type : str
            The unique identifier for the store type (e.g., 's3', 'sql').
        store : Store
            The factory used to create stores for this type.
        """
        if store_type not in self._builders:
            self._builders[store_type] = store
        else:
            raise StoreError(f"Store type {store_type} already registered")

    def get(self, uri: str) -> Store:
        """
        Get or create a store instance based on URI scheme.

        Determines the appropriate store type from the URI scheme,
        instantiates the store if not already cached, and returns
        the store instance. Store instances are cached for reuse.

        Parameters
        ----------
        uri : str
            The URI to parse for determining the store type.
            The scheme (e.g., 's3://', 'sql://') determines which
            store type to instantiate.

        Returns
        -------
        Store
            The store instance appropriate for handling the given URI.
        """
        store_type = map_uri_scheme(uri)

        # Build the store instance if not already present
        if store_type not in self._instances:
            self._instances[store_type] = self._builders[store_type]()

        return self._instances[store_type]


store_builder = StoreBuilder()
store_builder.register(SchemeCategory.S3.value, _build_s3_store)
store_builder.register(SchemeCategory.HF.value, _build_hf_store)
store_builder.register(SchemeCategory.SQL.value, _build_sql_store)
store_builder.register(SchemeCategory.LOCAL.value, _build_local_store)
store_builder.register(SchemeCategory.REMOTE.value, _build_remote_store)
