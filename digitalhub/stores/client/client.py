# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Iterator
from typing import Any

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.client.common.constants import PROXY_HOST_HEADER
from digitalhub.stores.client.common.enums import ConfigurationVars
from digitalhub.stores.client.executor.executor import ClientOpExecutor
from digitalhub.stores.client.http.handler import HttpRequestHandler
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.exceptions import ClientError

if typing.TYPE_CHECKING:
    from requests import Response

    from digitalhub.stores.client.auth.provider import AuthProvider
    from digitalhub.stores.client.compiler.operation import ClientOp
    from digitalhub.stores.client.http.transport import HttpTransport


class Client:
    """
    DHCore client for remote DigitalHub Core backend communication.

    Provides REST API communication with DigitalHub Core backend supporting
    multiple authentication methods: Basic (username/password), OAuth2 (token
    with refresh), and Personal Access Token exchange. Automatically handles
    API version compatibility, pagination, token refresh, error parsing, and
    JSON serialization.

    A client is cheap to build and holds no global state: the transport is
    shared and owned by whoever builds the client, the auth provider decides
    whose credentials the requests carry, and the configuration sets timeout
    and pagination.

    Parameters
    ----------
    transport : HttpTransport
        Connection pool, shared between clients and not closed by them.
    auth : AuthProvider
        Authenticates requests and resolves the endpoint.
    config : ClientConfig, optional
        Tunable settings. Defaults to ``ClientConfig()``, not to the global
        configuration.
    """

    def __init__(
        self,
        transport: HttpTransport,
        auth: AuthProvider,
        config: ClientConfig | None = None,
    ) -> None:
        """Initialize the client and its internal components."""
        self._config = config if config is not None else ClientConfig()
        self._transport = transport
        self._auth = auth
        self._http_handler = HttpRequestHandler(auth, transport, self._config)
        self._executor = ClientOpExecutor(self._http_handler, self._config)

    ##############################
    # CRUD methods
    ##############################

    def execute(self, request: ClientOp) -> Any:
        """Compile and execute one semantic backend operation request."""
        return self._executor.execute(request)

    def execute_list(self, request: ClientOp) -> list[dict[str, Any]]:
        """Compile and execute a paginated semantic list request."""
        return self._executor.execute_list(request)

    def iter_list(self, request: ClientOp) -> Iterator[dict[str, Any]]:
        """Yield a paginated semantic list without buffering all results."""
        return self._executor.iter_list(request)

    def execute_first(self, request: ClientOp) -> dict[str, Any]:
        """Compile and execute a list request, returning its first object."""
        return self._executor.execute_first(request)

    def proxy_request(self, host: str, method: str, path: str, **kwargs) -> Response:
        """
        Send a request to a cluster service through the proxy in front of Core.

        The request goes to ``path`` on the proxy configured with
        ``DHCORE_PROXY``, with the client's credentials and the service in the
        ``X-Proxy-Host`` header, and the response is returned without
        processing.

        Parameters
        ----------
        host : str
            Service to reach, as ``host:port``.
        method : str
            HTTP method.
        path : str
            Path of the request on the service.
        **kwargs : dict
            Keyword arguments of ``requests.request()``.

        Returns
        -------
        Response
            Response of the service.

        Raises
        ------
        ClientError
            If no proxy is configured.
        """
        proxy = self._auth.get_proxy()
        if proxy is None:
            raise ClientError(
                f"Service {host} cannot be reached from here and no proxy is configured: "
                f"set {ConfigurationVars.DHCORE_PROXY.value}."
            )
        headers = {**(kwargs.pop("headers", None) or {}), PROXY_HOST_HEADER: host}
        return self._http_handler.send(BackendReq.from_http(method, f"{proxy}{path}", headers=headers, **kwargs))

    ##############################
    # Facade methods
    ##############################

    def _identity(self) -> ClientConfigurator:
        """Return the user identity behind this client, for credential and profile operations."""
        if isinstance(self._auth, ClientConfigurator):
            return self._auth
        raise ClientError("Credentials and profiles are available only on a client of the user identity.")

    def eval_retry(self, check_token_validity: bool = False) -> bool:
        """
        Evaluate the status of retry lifecycle.
        """
        return self._identity().evaluate_refresh(check_token_validity=check_token_validity)

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.
        """
        return self._identity().get_credentials_and_config()

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.
        """
        self._identity().set_current_profile(profile)

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.
        """
        return self._identity().get_current_profile()

    def get_k8s_resource_profiles(self) -> list[str]:
        """
        Get the Kubernetes resource profile list from the current credentials.
        """
        return self._executor.get_k8s_resource_profiles()
