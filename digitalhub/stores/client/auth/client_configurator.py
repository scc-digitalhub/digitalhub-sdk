# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.auth.auth_session import AuthSession
from digitalhub.stores.client.auth.config_manager import ConfigManager
from digitalhub.stores.client.auth.refresh import TokenRefreshService
from digitalhub.stores.client.common.enums import AuthType
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.stores.client.http.transport import HttpTransport


class ClientConfigurator:
    """
    DHCore client configurator for credential management and authentication.

    Facade class that coordinates credential management, authentication handling,
    and token refresh operations. Delegates responsibilities to specialized
    components.

    Supports multiple authentication methods: EXCHANGE (personal access token),
    OAUTH2 (access + refresh tokens), ACCESS_TOKEN (access token only), and
    BASIC (username + password).

    The configurator automatically determines the best authentication method and
    handles token exchange for personal access tokens by switching to file-based
    credential storage.
    """

    def __init__(self, transport: HttpTransport) -> None:
        """
        Initialize DHCore configurator without performing network authentication.
        """
        self._config_manager = ConfigManager()
        self._auth_session = AuthSession(self._config_manager.credential_session)
        self._token_refresh_service = TokenRefreshService(
            self._config_manager,
            self._auth_session,
            transport,
        )
        self._exchange_bootstrapped = False

    ##############################
    # Credentials methods
    ##############################

    def get_endpoint(self) -> str:
        """
        Get the configured DHCore backend endpoint.

        Returns the sanitized and validated endpoint URL from current credential source.

        Returns
        -------
        str
            DHCore backend endpoint URL.
        """
        return self._config_manager.get_endpoint()

    ##############################
    # Auth methods
    ##############################

    def authenticate(self, backend_request: BackendReq) -> BackendReq:
        """Return an authenticated copy of a backend request."""
        if not self._exchange_bootstrapped:
            if self._auth_session.auth_type == AuthType.EXCHANGE.value:
                self.evaluate_refresh()
            self._exchange_bootstrapped = True
        return self._auth_session.authenticate(backend_request)

    def evaluate_refresh(self, check_token_validity: bool = False) -> bool:
        """
        Check if token refresh should be attempted.
        """
        return self._token_refresh_service.evaluate_refresh(check_token_validity=check_token_validity)

    ###############################
    # Utility methods
    ###############################

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.
        """
        return self._config_manager.get_credentials_and_config()

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.
        """
        self._config_manager.set_current_profile(profile)
        self._exchange_bootstrapped = False

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.
        """
        return self._config_manager.current_profile
