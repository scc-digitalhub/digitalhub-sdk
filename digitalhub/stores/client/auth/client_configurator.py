# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.auth.auth_session import AuthSession
from digitalhub.stores.client.auth.config_manager import ConfigManager
from digitalhub.stores.client.auth.refresh import TokenRefreshService
from digitalhub.stores.client.common.enums import AuthType


class ClientConfigurator:
    """
    DHCore client configurator for credential management and authentication.

    Facade class that coordinates credential management, authentication handling,
    and token refresh operations. Delegates responsibilities to specialized
    components while maintaining backward compatibility with existing interface.

    Supports multiple authentication methods: EXCHANGE (personal access token),
    OAUTH2 (access + refresh tokens), ACCESS_TOKEN (access token only), and
    BASIC (username + password).

    The configurator automatically determines the best authentication method and
    handles token exchange for personal access tokens by switching to file-based
    credential storage.
    """

    def __init__(self) -> None:
        """
        Initialize DHCore configurator and evaluate authentication type.
        """
        self._config_manager = ConfigManager()
        self._auth_session = AuthSession(self._config_manager.credential_session)
        self._token_refresh_service = TokenRefreshService(
            self._config_manager,
            self._auth_session,
        )
        self._bootstrap_authentication()

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

    def _bootstrap_authentication(self) -> None:
        """Exchange a personal access token during client initialization."""
        if self._auth_session.auth_type == AuthType.EXCHANGE.value:
            self.refresh_credentials()

    def get_auth_parameters(self, kwargs: dict | None = None) -> dict:
        """
        Add authentication headers/parameters to HTTP request kwargs.

        Adds Authorization Bearer header for token-based auth or auth tuple
        for basic authentication.

        Parameters
        ----------
        kwargs : dict
            HTTP request arguments to modify.

        Returns
        -------
        dict
            Modified kwargs with authentication parameters.
        """
        return self._auth_session.get_auth_parameters(kwargs)

    def refresh_credentials(self) -> None:
        """
        Refresh authentication tokens using OAuth2 flows.
        """
        self._token_refresh_service.refresh_credentials()

    def evaluate_refresh(self, check_token_validity: bool = False) -> bool:
        """
        Check if token refresh should be attempted.

        Parameters
        ----------
        check_token_validity : bool, optional
            Whether to check the validity of the token before attempting refresh.

        Returns
        -------
        bool
            True if credentials are ready for a request retry, otherwise False.
        """
        return self._token_refresh_service.evaluate_refresh(check_token_validity=check_token_validity)

    ###############################
    # Utility methods
    ###############################

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.

        Returns
        -------
        dict
            Current authentication credentials and configuration.
        """
        return self._config_manager.get_credentials_and_config()

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.

        Parameters
        ----------
        profile : str
            Name of the credentials profile to set.
        """
        self._config_manager.set_current_profile(profile)

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.

        Returns
        -------
        str
            Name of the current credentials profile.
        """
        return self._config_manager.current_profile