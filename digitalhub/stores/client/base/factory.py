# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from digitalhub.stores.client.base.client import Client

if TYPE_CHECKING:
    from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
    from digitalhub.stores.client.builders.api import ClientApiBuilder
    from digitalhub.stores.client.builders.key import ClientKeyBuilder
    from digitalhub.stores.client.builders.params import ClientParametersBuilder
    from digitalhub.stores.client.http.handler import HttpRequestHandler


class ClientFactory:
    """
    Client factory class. Creates and returns client instance with optional dependency injection.

    Implements singleton pattern for default client instance. Supports dependency injection
    for testing and customization scenarios.
    """

    def __init__(self) -> None:
        self._client: Client | None = None

    def build(
        self,
        configurator: ClientConfigurator | None = None,
        api_builder: ClientApiBuilder | None = None,
        key_builder: ClientKeyBuilder | None = None,
        params_builder: ClientParametersBuilder | None = None,
        http_handler: HttpRequestHandler | None = None,
    ) -> Client:
        """
        Create or return client instance with optional dependency injection.

        When called without arguments, returns singleton instance with default dependencies.
        When called with arguments, creates new instance with injected dependencies.

        Parameters
        ----------
        configurator : ClientConfigurator
            Configurator for credentials and authentication.
        api_builder : ClientApiBuilder
            Builder for API endpoints.
        key_builder : ClientKeyBuilder
            Builder for entity keys.
        params_builder : ClientParametersBuilder
            Builder for request parameters.
        http_handler : HttpRequestHandler
            Handler for HTTP requests.

        Returns
        -------
        Client
            Client instance with specified or default dependencies.
        """
        # If any dependency is provided, create new instance with those dependencies
        if any(
            dep is not None
            for dep in [
                configurator,
                api_builder,
                key_builder,
                params_builder,
                http_handler,
            ]
        ):
            return Client(
                configurator=configurator,
                api_builder=api_builder,
                key_builder=key_builder,
                params_builder=params_builder,
                http_handler=http_handler,
            )

        # Otherwise, return singleton instance with defaults
        if self._client is None:
            self._client = Client()
        return self._client


client_factory = ClientFactory()


def get_client(
    configurator: ClientConfigurator | None = None,
    api_builder: ClientApiBuilder | None = None,
    key_builder: ClientKeyBuilder | None = None,
    params_builder: ClientParametersBuilder | None = None,
    http_handler: HttpRequestHandler | None = None,
) -> Client:
    """
    Get client instance with optional dependency injection.

    Wrapper around ClientFactory.build. When called without arguments, returns
    singleton instance. When called with dependencies, creates new instance.

    Parameters
    ----------
    configurator : ClientConfigurator
        Configurator for credentials and authentication.
    api_builder : ClientApiBuilder
        Builder for API endpoints.
    key_builder : ClientKeyBuilder
        Builder for entity keys.
    params_builder : ClientParametersBuilder
        Builder for request parameters.
    http_handler : HttpRequestHandler
        Handler for HTTP requests.

    Returns
    -------
    Client
        The client instance.

    Examples
    --------
    Get default singleton client:
    >>> client = get_client()

    Create client with custom configurator for testing:
    >>> mock_configurator = MockClientConfigurator()
    >>> test_client = get_client(configurator=mock_configurator)
    """
    return client_factory.build(
        configurator=configurator,
        api_builder=api_builder,
        key_builder=key_builder,
        params_builder=params_builder,
        http_handler=http_handler,
    )
