# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.client import Client


class ClientFactory:
    """
    Client factory class responsible for the default singleton instance.
    """

    def __init__(self) -> None:
        self._client: Client | None = None

    def reset(self) -> None:
        self._client = None

    def build(self) -> Client:
        """
        Create or return the default singleton client.

        Returns
        -------
        Client
            The shared client instance.
        """
        if self._client is None:
            self._client = Client()
        return self._client


client_factory = ClientFactory()


def get_client() -> Client:
    """
    Get the default singleton client.

    Returns
    -------
    Client
        The client instance.

    Examples
    --------
    Get default singleton client:
    >>> client = get_client()

    """
    return client_factory.build()
