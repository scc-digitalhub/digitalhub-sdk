# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.executor.executor import ClientOpExecutor
from digitalhub.stores.client.http.handler import HttpRequestHandler
from digitalhub.stores.client.http.transport import HttpTransport


class Client:
    """
    DHCore client for remote DigitalHub Core backend communication.

    Provides REST API communication with DigitalHub Core backend supporting
    multiple authentication methods: Basic (username/password), OAuth2 (token
    with refresh), and Personal Access Token exchange. Automatically handles
    API version compatibility, pagination, token refresh, error parsing, and
    JSON serialization.
    """

    def __init__(self) -> None:
        """Initialize the client and its internal components."""
        self._transport = HttpTransport()
        self._configurator = ClientConfigurator(self._transport)
        self._http_handler = HttpRequestHandler(self._configurator, self._transport)
        self._executor = ClientOpExecutor(self._http_handler)

    ##############################
    # CRUD methods
    ##############################

    def execute(self, request: ClientOp) -> Any:
        """Compile and execute one semantic backend operation request."""
        return self._executor.execute(request)

    def execute_list(self, request: ClientOp) -> list[dict[str, Any]]:
        """Compile and execute a paginated semantic list request."""
        return self._executor.execute_list(request)

    def execute_first(self, request: ClientOp) -> dict[str, Any]:
        """Compile and execute a list request, returning its first object."""
        return self._executor.execute_first(request)

    ##############################
    # Facade methods
    ##############################

    def eval_retry(self, check_token_validity: bool = False) -> bool:
        """
        Evaluate the status of retry lifecycle.
        """
        return self._configurator.evaluate_refresh(check_token_validity=check_token_validity)

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.
        """
        return self._configurator.get_credentials_and_config()

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.
        """
        self._configurator.set_current_profile(profile)

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.
        """
        return self._configurator.get_current_profile()

    def get_k8s_resource_profiles(self) -> list[str]:
        """
        Get the Kubernetes resource profile list from the current credentials.
        """
        return self._executor.get_k8s_resource_profiles()
