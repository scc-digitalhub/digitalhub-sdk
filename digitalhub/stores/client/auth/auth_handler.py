# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client.auth.enums import CredentialsVars
from digitalhub.stores.client.common.enums import AuthType
from digitalhub.stores.client.common.utils import ensure_headers

if typing.TYPE_CHECKING:
    from digitalhub.stores.client.auth.config_manager import ConfigManager


class AuthenticationHandler:
    """
    Handles authentication type evaluation and parameter injection.

    Determines the appropriate authentication method from available credentials
    and adds authentication headers/parameters to HTTP requests. Supports
    multiple authentication methods: EXCHANGE (personal access token), OAUTH2
    (access + refresh tokens), ACCESS_TOKEN (access only), and BASIC
    (username + password).
    """

    def __init__(self, credential_manager: ConfigManager) -> None:
        """
        Initialize authentication handler.

        Parameters
        ----------
        credential_manager : CredentialManager
            Credential manager instance for accessing credentials.
        """
        self._credential_manager = credential_manager
        self._auth_type: str | None = None
        self.evaluate_auth_type()

    def evaluate_auth_type(self) -> None:
        """
        Determine authentication type from available credentials.

        Evaluates credentials in priority order: EXCHANGE (personal access token),
        OAUTH2 (access + refresh tokens), ACCESS_TOKEN (access only), BASIC
        (username + password).
        """
        creds = self._credential_manager.get_credentials()
        self._auth_type = self._eval_auth_type(creds)

    @property
    def auth_type(self) -> str | None:
        """
        Get current authentication type.

        Returns
        -------
        str or None
            Current authentication type from AuthType enum.
        """
        return self._auth_type

    def is_refreshable(self) -> bool:
        """
        Check if current authentication supports token refresh.

        Returns True for OAUTH2 (refresh token) and EXCHANGE (personal access token),
        False for BASIC and ACCESS_TOKEN.

        Returns
        -------
        bool
            Whether authentication type supports refresh.
        """
        return self._auth_type in [AuthType.OAUTH2.value, AuthType.EXCHANGE.value]

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
        creds = self._credential_manager.get_credentials()
        if self._auth_type in (
            AuthType.EXCHANGE.value,
            AuthType.OAUTH2.value,
            AuthType.ACCESS_TOKEN.value,
        ):
            access_token = creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value]
            kwargs = ensure_headers(**kwargs)
            kwargs["headers"]["Authorization"] = f"Bearer {access_token}"
        elif self._auth_type == AuthType.BASIC.value:
            user = creds[CredentialsVars.DHCORE_USER.value]
            password = creds[CredentialsVars.DHCORE_PASSWORD.value]
            kwargs["auth"] = (user, password)
        return kwargs

    def _eval_auth_type(self, creds: dict) -> str | None:
        """
        Determine authentication type from available credentials.

        Evaluates in priority order:

            EXCHANGE (personal access token)
            OAUTH2 (access + refresh tokens)
            ACCESS_TOKEN (access only)
            BASIC (username + password)
            None (no valid credentials type)

        Parameters
        ----------
        creds : dict
            Available credential values.

        Returns
        -------
        str or None
            Authentication type from AuthType enum, or None if no valid credentials.
        """
        if creds[CredentialsVars.DHCORE_PERSONAL_ACCESS_TOKEN.value] is not None:
            return AuthType.EXCHANGE.value
        if (
            creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value] is not None
            and creds[CredentialsVars.DHCORE_REFRESH_TOKEN.value] is not None
        ):
            return AuthType.OAUTH2.value
        if creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value] is not None:
            return AuthType.ACCESS_TOKEN.value
        if (
            creds[CredentialsVars.DHCORE_USER.value] is not None
            and creds[CredentialsVars.DHCORE_PASSWORD.value] is not None
        ):
            return AuthType.BASIC.value
        return None
