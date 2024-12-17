from __future__ import annotations

import typing
from abc import abstractmethod

if typing.TYPE_CHECKING:
    from digitalhub.client._base.api_builder import ClientApiBuilder
    from digitalhub.client._base.key_builder import ClientKeyBuilder


class Client:
    """
    Base Client class interface.

    The client is an interface that handles the CRUD of an object during
    a session. It manages the creation, reading, updating, deleting and
    listing of objects and comes into two subclasses: Local and DHCore.
    """

    def __init__(self) -> None:
        self._api_builder: ClientApiBuilder = None
        self._key_builder: ClientKeyBuilder = None

    ##############################
    # CRUD methods
    ##############################

    @abstractmethod
    def create_object(self, api: str, obj: dict, **kwargs) -> dict:
        """
        Create object method.
        """

    @abstractmethod
    def read_object(self, api: str, **kwargs) -> dict:
        """
        Read object method.
        """

    @abstractmethod
    def update_object(self, api: str, obj: dict, **kwargs) -> dict:
        """
        Update object method.
        """

    @abstractmethod
    def delete_object(self, api: str, **kwargs) -> dict:
        """
        Delete object method.
        """

    @abstractmethod
    def list_objects(self, api: str, **kwargs) -> dict:
        """
        List objects method.
        """

    @abstractmethod
    def list_first_object(self, api: str, **kwargs) -> dict:
        """
        Read first object method.
        """

    @abstractmethod
    def search_objects(self, api: str, **kwargs) -> dict:
        """
        Search objects method.
        """

    ##############################
    # Build methods
    ##############################

    def build_api(self, category: str, operation: str, **kwargs) -> str:
        """
        Build the API for the client.

        Parameters
        ----------
        category : str
            API category.
        operation : str
            API operation.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            API formatted.
        """
        return self._api_builder.build_api(category, operation, **kwargs)

    def build_key(self, category: str, *args, **kwargs) -> str:
        """
        Build the key for the client.

        Parameters
        ----------
        category : str
            Key category.
        *args : tuple
            Additional arguments.
        **kwargs : dict
            Additional parameters.

        Returns
        -------
        str
            Key formatted.
        """
        return self._key_builder.build_key(category, *args, **kwargs)

    ##############################
    # Interface methods
    ##############################

    @staticmethod
    @abstractmethod
    def is_local() -> bool:
        """
        Flag to check if client is local.
        """
