# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from requests import get, post

from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import AuthType
from digitalhub.stores.client.common.utils import sanitize_endpoint, set_urlencoded_content_type
from digitalhub.utils.exceptions import ClientError

if typing.TYPE_CHECKING:
    from requests import Response

    from digitalhub.stores.client.auth.auth_handler import AuthenticationHandler
    from digitalhub.stores.client.auth.config_manager import ConfigManager


class TokenRefreshService:
    """
    Handles OAuth2 token refresh operations for DHCore client.

    Manages token exchange for personal access tokens and refresh token
    operations for OAuth2 authentication. Automatically discovers token
    endpoints from OAuth2 issuer well-known configuration and persists
    refreshed credentials.
    """

    def __init__(
        self,
        credential_manager: ConfigManager,
        authentication_handler: AuthenticationHandler,
    ) -> None:
        """
        Initialize token refresh service.

        Parameters
        ----------
        credential_manager : CredentialManager
            Credential manager for accessing and persisting credentials.
        authentication_handler : AuthenticationHandler
            Authentication handler for checking auth type.
        """
        self._credential_manager = credential_manager
        self._authentication_handler = authentication_handler

    def refresh_credentials(self) -> None:
        """
        Refresh authentication tokens using OAuth2 flows.

        Exchanges personal access tokens or refreshes OAuth2 tokens depending
        on the current authentication type. Persists new credentials to file.

        Raises
        ------
        ClientError
            If authentication type doesn't support refresh or refresh fails.
        """
        if not self._authentication_handler.is_refreshable():
            raise ClientError(f"Auth type {self._authentication_handler.auth_type} does not support refresh.")

        # Get credentials and configuration
        creds = self._credential_manager.get_credentials_and_config()

        # Get token refresh endpoint
        if (url := creds.get(ConfigurationVars.OAUTH2_TOKEN_ENDPOINT.value)) is None:
            url = self._get_refresh_endpoint()
        url = sanitize_endpoint(url)

        # Execute the appropriate auth flow
        response = self._evaluate_auth_flow(url, creds)

        # Raise an error if the response indicates failure
        response.raise_for_status()

        # Export new credentials to file
        self._export_new_creds(response.json())

        # Reload credentials and re-evaluate auth type
        self._credential_manager.reload_credentials()
        self._authentication_handler.evaluate_auth_type()

    def evaluate_refresh(self) -> bool:
        """
        Check if token refresh should be attempted with retry logic.

        Attempts to refresh credentials, and if it fails, retries with
        credentials from alternate sources (file vs environment).

        Returns
        -------
        bool
            True if token refresh succeeded, False if all attempts failed.
        """
        try:
            self.refresh_credentials()
            return True
        except Exception:
            if not self._credential_manager.eval_retry():
                warn(
                    "Failed to refresh credentials after retry"
                    " (checked credentials from file and env)."
                    " Please check your credentials"
                    " and make sure they are up to date."
                    " (refresh tokens, password, etc.)."
                )
                return False
            return self.evaluate_refresh()

    def _evaluate_auth_flow(self, url: str, creds: dict) -> Response:
        """
        Execute appropriate OAuth2 flow based on authentication type.

        Parameters
        ----------
        url : str
            Token endpoint URL.
        creds : dict
            Available credential values.

        Returns
        -------
        Response
            HTTP response from token endpoint.

        Raises
        ------
        ClientError
            If client_id is not configured.
        """
        if (client_id := creds.get(ConfigurationVars.DHCORE_CLIENT_ID.value)) is None:
            raise ClientError("Client id not set.")

        auth_type = self._authentication_handler.auth_type

        # Handling of token refresh
        if auth_type == AuthType.OAUTH2.value:
            return self._call_refresh_endpoint(
                url,
                client_id=client_id,
                refresh_token=creds.get(CredentialsVars.DHCORE_REFRESH_TOKEN.value),
                grant_type=get_client_config().oauth2_grant_type,
                scope=get_client_config().oauth2_scope,
            )

        # Handling of token exchange
        return self._call_refresh_endpoint(
            url,
            client_id=client_id,
            subject_token=creds.get(CredentialsVars.DHCORE_PERSONAL_ACCESS_TOKEN.value),
            subject_token_type=get_client_config().pat_subject_token_type,
            grant_type=get_client_config().pat_grant_type,
            scope=get_client_config().pat_scope,
        )

    def _get_refresh_endpoint(self) -> str:
        """
        Discover OAuth2 token endpoint from issuer well-known configuration.

        Queries /.well-known/openid-configuration to extract token_endpoint for
        credential refresh operations.

        Returns
        -------
        str
            Token endpoint URL for credential refresh.

        Raises
        ------
        ClientError
            If issuer endpoint is not configured.
        """
        config = self._credential_manager.get_configuration()

        # Get issuer endpoint
        if (endpoint_issuer := config.get(ConfigurationVars.DHCORE_ISSUER.value)) is None:
            raise ClientError("Issuer endpoint not set.")

        # Standard issuer endpoint path
        url = sanitize_endpoint(endpoint_issuer + "/.well-known/openid-configuration")

        # Call issuer to get refresh endpoint
        r = get(url, timeout=get_client_config().http_timeout)
        r.raise_for_status()
        return r.json().get("token_endpoint")

    def _call_refresh_endpoint(
        self,
        url: str,
        **kwargs,
    ) -> Response:
        """
        Make OAuth2 token refresh request.

        Sends POST request with form-encoded payload using required OAuth2
        content type and 60-second timeout.

        Parameters
        ----------
        url : str
            Token endpoint URL.
        **kwargs : dict
            Token request parameters (grant_type, client_id, etc.).

        Returns
        -------
        Response
            Raw HTTP response for caller handling.
        """
        req_kwargs = {"data": kwargs, **set_urlencoded_content_type()}
        return post(url, timeout=get_client_config().http_timeout, **req_kwargs)

    def _export_new_creds(self, response: dict) -> None:
        """
        Save refreshed credentials and switch to file-based storage.

        Persists new tokens (access_token, refresh_token, etc.) to configuration
        file with proper key formatting.

        Parameters
        ----------
        response : dict
            OAuth2 token response with new credentials.
        """
        keys_to_prefix = [
            CredentialsVars.DHCORE_REFRESH_TOKEN.value,
            CredentialsVars.DHCORE_ACCESS_TOKEN.value,
            ConfigurationVars.DHCORE_CLIENT_ID.value,
            ConfigurationVars.DHCORE_ISSUER.value,
            ConfigurationVars.OAUTH2_TOKEN_ENDPOINT.value,
        ]
        for key in keys_to_prefix:
            if key == ConfigurationVars.OAUTH2_TOKEN_ENDPOINT.value:
                prefix = get_client_config().oauth2
            else:
                prefix = get_client_config().dhcore
            key = key.lower()
            if key.removeprefix(prefix) in response:
                response[key] = response.pop(key.removeprefix(prefix))
        self._credential_manager.write_credentials(response)
