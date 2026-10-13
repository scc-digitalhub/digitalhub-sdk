# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from dataclasses import replace

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import (
    AuthType,
    ConfigurationVars,
    CredentialsVars,
    OpsType,
)
from digitalhub.stores.client.common.utils import sanitize_endpoint, with_urlencoded_content_type
from digitalhub.stores.client.http.errors import raise_for_response_error
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.stores.client.http.response import parse_response_json
from digitalhub.utils.exceptions import BackendError, ClientError
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from requests import Response

    from digitalhub.stores.client.auth.auth_session import AuthSession
    from digitalhub.stores.client.auth.config_manager import ConfigManager
    from digitalhub.stores.client.http.transport import HttpTransport

logger = get_logger(__name__)


class TokenRefreshService:
    """
    Handles OAuth2 token refresh operations for DHCore client.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        auth_session: AuthSession,
        transport: HttpTransport,
    ) -> None:
        self._config_manager = config_manager
        self._auth_session = auth_session
        self._transport = transport

    def refresh_credentials(self) -> None:
        """
        Refresh authentication tokens using OAuth2 flows.

        Exchanges personal access tokens or refreshes OAuth2 tokens depending
        on the current authentication type. Persists new credentials to file.
        """
        if not self._auth_session.is_refreshable():
            raise ClientError(f"Auth type {self._auth_session.auth_type} does not support refresh.")

        logger.debug(f"Starting creds refresh with auth type '{self._auth_session.auth_type}'.")

        # Get credentials and configuration
        creds = self._config_manager.get_credentials_and_config()

        # Get token refresh endpoint
        if (url := creds.get(ConfigurationVars.OAUTH2_TOKEN_ENDPOINT.value)) is None:
            url = self._get_refresh_endpoint()
        url = sanitize_endpoint(url)
        logger.debug("Refresh endpoint resolved; sending creds refresh request.")

        # Execute the appropriate auth flow
        response = self._evaluate_auth_flow(url, creds)

        # Raise an error if the response indicates failure
        raise_for_response_error(response)

        refreshed_credentials = parse_response_json(response)
        logger.debug(f"Refresh request succeeded; persisting fields: {sorted(refreshed_credentials)}")

        # Export new credentials to file
        self._config_manager.save_refreshed_credentials(refreshed_credentials)

        logger.debug("Creds refresh completed successfully.")

    def evaluate_refresh(self, check_token_validity: bool = False) -> bool:
        """
        Refresh the active credentials and report whether a refresh or fallback succeeded.

        When ``check_token_validity`` is true, validate the current access token
        first. If it is valid, return false without attempting a refresh.
        Otherwise, attempt to refresh credentials up to the configured maximum,
        switching credential sources when the retry policy allows it.

        Returns
        -------
        bool
            True if credentials were refreshed or a valid environment access
            token was confirmed. False if no refresh was needed because the
            current token was valid, or if environment fallback credentials
            cannot be refreshed or used.
        """
        if check_token_validity:
            if self._test_token_validity():
                logger.debug("Current token is valid, no refresh needed.")
                return False
            logger.debug("Current token is invalid or expired, attempting refresh.")

        max_attempts = get_client_config().max_refresh_attempts

        for attempt in range(1, max_attempts + 1):
            logger.debug(f"Starting creds refresh attempt {attempt}.")
            try:
                self.refresh_credentials()
            except (BackendError, ClientError) as error:
                logger.debug(
                    f"Creds refresh attempt {attempt} failed with {type(error).__name__}; evaluating fallback.",
                    exc_info=True,
                )
                if attempt == max_attempts:
                    logger.debug(f"Creds refresh stopped after max attempts ({max_attempts}).")
                    raise

                # Check if we should retry based on the configuration manager's evaluation
                was_using_env = self._config_manager.is_using_env()
                should_retry = self._config_manager.eval_retry()
                logger.debug(f"Creds refresh fallback decision after attempt {attempt}: {should_retry}.")
                if not should_retry:
                    logger.debug(f"Creds refresh stopped after attempt {attempt}.")
                    raise

                # Determine if we have switched to using environment credentials
                switched_to_env = not was_using_env and self._config_manager.is_using_env()
                if switched_to_env:
                    match self._auth_session.auth_type:
                        case AuthType.EXCHANGE.value:
                            continue
                        case AuthType.OAUTH2.value:
                            if self._test_token_validity():
                                logger.debug("Env access token is valid; skipping refresh.")
                                return True
                        case AuthType.ACCESS_TOKEN.value:
                            if self._test_token_validity():
                                logger.debug("Env access token is valid; skipping refresh.")
                                return True
                            logger.debug("Env access token is invalid and there is no refresh token.")
                            return False
                        case _:
                            logger.debug("Env creds are not refreshable; stopping refresh fallback.")
                            return False
            else:
                logger.debug(f"Creds refresh attempt {attempt} succeeded.")
                return True

    def _test_token_validity(self) -> bool:
        """
        Test the validity of the current access token.
        """
        url = self._config_manager.configuration.get(ConfigurationVars.DHCORE_ENDPOINT.value)
        if url is None:
            raise ClientError("API endpoint not set.")
        url = sanitize_endpoint(url) + get_client_config().api_auth_check

        backend_request = self._auth_session.authenticate(
            BackendReq.get(
                api=url,
                operation=OpsType.AUTH_VALIDATE,
            ),
        )
        response = self._transport.execute(replace(backend_request, authenticate=False))

        return response.status_code == 200

    def _evaluate_auth_flow(self, url: str, creds: dict) -> Response:
        """
        Execute appropriate OAuth2 flow based on authentication type.
        """
        if (client_id := creds.get(ConfigurationVars.DHCORE_CLIENT_ID.value)) is None:
            raise ClientError("Client id not set.")

        # Handling of token refresh
        match self._auth_session.auth_type:
            case AuthType.OAUTH2.value:
                data = {
                    "client_id": client_id,
                    "refresh_token": creds.get(CredentialsVars.DHCORE_REFRESH_TOKEN.value),
                    "grant_type": get_client_config().oauth2_grant_type,
                    "scope": get_client_config().oauth2_scope,
                }
            case AuthType.EXCHANGE.value:
                data = {
                    "client_id": client_id,
                    "subject_token": creds.get(CredentialsVars.DHCORE_PERSONAL_ACCESS_TOKEN.value),
                    "subject_token_type": get_client_config().pat_subject_token_type,
                    "grant_type": get_client_config().pat_grant_type,
                    "scope": get_client_config().pat_scope,
                }
            case _:
                raise ClientError(f"Unsupported authentication type: {self._auth_session.auth_type}")

        request = BackendReq.post(
            api=url,
            operation=OpsType.AUTH_REFRESH,
            data=data,
            authenticate=False,
        )
        return self._transport.execute(with_urlencoded_content_type(request))

    def _get_refresh_endpoint(self) -> str:
        """
        Discover OAuth2 token endpoint from issuer well-known configuration.

        Queries /.well-known/openid-configuration to extract token_endpoint for
        creds refresh operations.

        Returns
        -------
        str
            Token endpoint URL for creds refresh.
        """
        endpoint_issuer = self._config_manager.configuration.get(ConfigurationVars.DHCORE_ISSUER.value)

        # Get issuer endpoint
        if endpoint_issuer is None:
            raise ClientError("Issuer endpoint not set.")

        # Standard issuer endpoint path
        url = sanitize_endpoint(endpoint_issuer + get_client_config().well_known_openid_conf)

        # Call issuer to get refresh endpoint
        response = self._transport.execute(
            BackendReq.get(
                api=url,
                operation=OpsType.AUTH_DISCOVERY,
                authenticate=False,
            ),
        )

        raise_for_response_error(response)
        discovery = parse_response_json(response)
        token_endpoint = discovery.get("token_endpoint") if isinstance(discovery, dict) else None
        if not isinstance(token_endpoint, str) or not token_endpoint.strip():
            raise ClientError("Token endpoint not set.")
        return token_endpoint
