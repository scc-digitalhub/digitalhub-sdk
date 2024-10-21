from __future__ import annotations

import typing

from digitalhub.client.dhcore.client import ClientDHCore
from digitalhub.client.local.client import ClientLocal

if typing.TYPE_CHECKING:
    from digitalhub.client._base.client import Client


class ClientBuilder:
    """
    Client builder class.

    This class is used to create two possible client instances:
    Local and DHCore.
    It saves the client instances in the class attributes using
    singleton pattern.
    """

    def __init__(self) -> None:
        self._local = None
        self._dhcore = None

    def build(self, local: bool = False, config: dict | None = None) -> Client:
        """
        Method to create a client instance.

        Parameters
        ----------
        local : bool
            Whether to create a local client or not.

        Returns
        -------
        Client
            Returns the client instance.
        """
        if local:
            if self._local is None:
                self._local = ClientLocal()
            return self._local

        if self._dhcore is None:
            self._dhcore = ClientDHCore(config)
        return self._dhcore


client_builder = ClientBuilder()
