from __future__ import annotations

import typing

from digitalhub.datastores.local.datastore import LocalDatastore
from digitalhub.datastores.remote.datastore import RemoteDatastore
from digitalhub.datastores.s3.datastore import S3Datastore
from digitalhub.datastores.sql.datastore import SqlDatastore
from digitalhub.stores.api import get_default_store, get_store
from digitalhub.utils.uri_utils import map_uri_scheme

if typing.TYPE_CHECKING:
    from digitalhub.datastores._base.datastore import Datastore
    from digitalhub.stores._base.store import Store


REGISTRY_DATASTORES = {
    "local": LocalDatastore,
    "remote": RemoteDatastore,
    "s3": S3Datastore,
    "sql": SqlDatastore,
}


class DatastoreBuilder:
    """
    Datastore builder class.
    """

    def __init__(self) -> None:
        self._instances: dict[str, Datastore] = {}
        self._default: Datastore | None = None
        self._def_scheme = "s3"

    def build(self, uri: str) -> None:
        """
        Build a datastore instance and register it.
        It overrides any existing instance.

        Parameters
        ----------
        uri : str
            URI to parse.

        Returns
        -------
        None
        """
        store = get_store(uri)
        self._instances[store.type] = self.build_datastore(store)

    def get(self, uri: str) -> Datastore:
        """
        Get a store instance by URI.

        Parameters
        ----------
        uri : str
            URI to parse.

        Returns
        -------
        Datastore
            The datastore instance.
        """
        scheme = map_uri_scheme(uri)
        if scheme not in self._instances:
            self.build(uri)
        return self._instances[scheme]

    def default(self) -> Datastore:
        """
        Get the default store instance.

        Returns
        -------
        Datastore
            The default datastore instance.
        """
        if self._default is None:
            store = get_default_store()
            self._default = self.build_datastore(store)
        return self._default

    def build_datastore(self, store: Store) -> Datastore:
        """
        Build a datastore instance.

        Parameters
        ----------
        store : Store
            Store instance.

        Returns
        -------
        Datastore
            The datastore instance.

        Raises
        ------
        NotImplementedError
            If the store type is not implemented.
        """
        try:
            return REGISTRY_DATASTORES[store.type](store)
        except KeyError as e:
            raise NotImplementedError from e


builder = DatastoreBuilder()
