# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from requests import get

from digitalhub.stores.client.auth.auth_handler import AuthenticationHandler
from digitalhub.stores.client.auth.config_manager import ConfigManager
from digitalhub.stores.client.auth.refresh import TokenRefreshService
from digitalhub.stores.client.common.config import get_client_config
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
        self._cfg_manager = ConfigManager()
        self._auth_handler = AuthenticationHandler(self._cfg_manager)
        self._token_refresh_service = TokenRefreshService(
            self._cfg_manager,
            self._auth_handler,
        )
        self.set_auth_type()

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

        Raises
        ------
        KeyError
            If endpoint not configured in current credential source.
        """
        return self._cfg_manager.get_endpoint()

    ##############################
    # Auth methods
    ##############################

    def set_auth_type(self) -> None:
        """
        Determine authentication type from available credentials.

        Evaluates credentials in priority order: EXCHANGE (personal access token),
        OAUTH2 (access + refresh tokens), ACCESS_TOKEN (access only), BASIC
        (username + password). For EXCHANGE type, automatically exchanges the
        personal access token and switches to file-based credentials storage.
        """
        # Initial evaluation
        self._auth_handler.evaluate_auth_type()

        # If we have an exchange token, we need to get a new access token.
        # Therefore, we change the origin to file, where the refresh token is written.
        if self._auth_handler.auth_type == AuthType.EXCHANGE.value:
            self.refresh_credentials()

    def refreshable_auth_types(self) -> bool:
        """
        Check if current authentication supports token refresh.

        Returns True for OAUTH2 (refresh token) and EXCHANGE (personal access token),
        False for BASIC and ACCESS_TOKEN.

        Returns
        -------
        bool
            Whether authentication type supports refresh.
        """
        return self._auth_handler.is_refreshable()

    def get_auth_parameters(self, kwargs: dict) -> dict:
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
        return self._auth_handler.get_auth_parameters(kwargs)

    def refresh_credentials(self) -> None:
        """
        Refresh authentication tokens using OAuth2 flows.
        """
        self._token_refresh_service.refresh_credentials()

    def evaluate_refresh(self) -> bool:
        """
        Check if token refresh should be attempted.

        Returns
        -------
        bool
            True if token refresh is applicable, otherwise False.
        """
        return self._token_refresh_service.evaluate_refresh()

    ###############################
    # Utility methods
    ###############################

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.
        Evaluate credentials validity before returning.

        Returns
        -------
        dict
            Current authentication credentials and configuration.
        """
        url = self.get_endpoint() + "/api/auth"

        # Handle authentication errors with token refresh
        kwargs = self.get_auth_parameters({})
        response = get(url, timeout=get_client_config().http_timeout, **kwargs)
        try:
            response.raise_for_status()
        except Exception as e:
            if response.status_code == 401 and self.evaluate_refresh():
                kwargs = self.get_auth_parameters({})
                return get(url, timeout=get_client_config().http_timeout, **kwargs)
            raise e
        return self._cfg_manager.get_credentials_and_config()

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.

        Parameters
        ----------
        profile : str
            Name of the credentials profile to set.
        """
        self._cfg_manager.set_current_profile(profile)
        self._auth_handler.evaluate_auth_type()

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.

        Returns
        -------
        str
            Name of the current credentials profile.
        """
        return self._cfg_manager.get_current_profile()
