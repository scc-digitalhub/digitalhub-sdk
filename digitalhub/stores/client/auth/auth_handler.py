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
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager
        self._auth_type: str = self._eval_auth_type()

    def evaluate_auth_type(self) -> None:
        """
        Determine authentication type from available credentials.
        """
        self._auth_type = self._eval_auth_type()

    def _eval_auth_type(self) -> str:
        """
        Evaluates in priority order:

            EXCHANGE (personal access token)
            OAUTH2 (access + refresh tokens)
            ACCESS_TOKEN (access only)
            BASIC (username + password)
            NO_AUTH (no authentication)

        Returns
        -------
        str
            Authentication type from AuthType enum.
        """
        creds = self._config_manager.credentials

        # PAT
        if creds[CredentialsVars.DHCORE_PERSONAL_ACCESS_TOKEN.value] is not None:
            return AuthType.EXCHANGE.value

        # OAuth2 if refresh token is present, otherwise access token only
        if creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value] is not None:
            if creds[CredentialsVars.DHCORE_REFRESH_TOKEN.value] is not None:
                return AuthType.OAUTH2.value
            return AuthType.ACCESS_TOKEN.value

        # Basic auth
        if (
            creds[CredentialsVars.DHCORE_USER.value] is not None
            and creds[CredentialsVars.DHCORE_PASSWORD.value] is not None
        ):
            return AuthType.BASIC.value

        # No auth
        return AuthType.NO_AUTH.value

    def is_refreshable(self) -> bool:
        """
        Check if current authentication supports token refresh.

        Returns True for OAUTH2 (refresh token) and EXCHANGE (personal access token).

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
        creds = self._config_manager.credentials

        match self._auth_type:
            case AuthType.EXCHANGE.value | AuthType.OAUTH2.value | AuthType.ACCESS_TOKEN.value:
                access_token = creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value]
                kwargs = ensure_headers(**kwargs)
                kwargs["headers"]["Authorization"] = f"Bearer {access_token}"
            case AuthType.BASIC.value:
                user = creds[CredentialsVars.DHCORE_USER.value]
                password = creds[CredentialsVars.DHCORE_PASSWORD.value]
                kwargs["auth"] = (user, password)
            case _:
                pass
        return kwargs

    ###############################
    # Properties
    ###############################

    @property
    def auth_type(self) -> str:
        return self._auth_type
