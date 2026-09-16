# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest
from requests import Response

import digitalhub.stores.client.auth.refresh as refresh_module
from digitalhub.stores.client.auth.refresh import TokenRefreshService
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import (
    AuthType,
    ConfigurationVars,
    CredentialSource,
    CredentialsVars,
    OpsType,
)
from digitalhub.stores.client.http.request import BERequest
from digitalhub.utils.exceptions import BadRequestError, ClientError


def test_evaluate_refresh_propagates_unexpected_errors() -> None:
    config_manager = Mock()
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock(side_effect=RuntimeError("internal failure"))

    with pytest.raises(RuntimeError, match="internal failure"):
        service.evaluate_refresh()

    config_manager.eval_retry.assert_not_called()


def test_evaluate_refresh_retries_expected_credential_errors() -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock(side_effect=[ClientError("invalid credentials"), None])

    assert service.evaluate_refresh() is True
    assert service.refresh_credentials.call_count == 2
    config_manager.eval_retry.assert_called_once_with()


def test_evaluate_refresh_retries_normalized_backend_errors() -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock(side_effect=[BadRequestError("refresh token does not exist"), None])

    assert service.evaluate_refresh() is True
    assert service.refresh_credentials.call_count == 2
    config_manager.eval_retry.assert_called_once_with()


def test_evaluate_refresh_stops_for_non_refreshable_environment_credentials() -> None:
    config_manager = Mock(credential_source=CredentialSource.FILE)

    def switch_to_environment() -> bool:
        config_manager.credential_source = CredentialSource.ENV
        return True

    config_manager.eval_retry.side_effect = switch_to_environment
    auth_session = Mock(auth_type=AuthType.BASIC.value)
    service = TokenRefreshService(config_manager, auth_session, Mock())
    service.refresh_credentials = Mock(side_effect=ClientError("file credentials expired"))

    assert service.evaluate_refresh() is False
    service.refresh_credentials.assert_called_once_with()


def test_evaluate_refresh_accepts_a_valid_environment_token() -> None:
    config_manager = Mock(credential_source=CredentialSource.FILE)

    def switch_to_environment() -> bool:
        config_manager.credential_source = CredentialSource.ENV
        return True

    config_manager.eval_retry.side_effect = switch_to_environment
    auth_session = Mock(auth_type=AuthType.OAUTH2.value)
    service = TokenRefreshService(config_manager, auth_session, Mock())
    service.refresh_credentials = Mock(side_effect=ClientError("file credentials expired"))
    service._test_token_validity = Mock(return_value=True)

    assert service.evaluate_refresh() is True
    service.refresh_credentials.assert_called_once_with()
    service._test_token_validity.assert_called_once_with()


def test_evaluate_refresh_propagates_error_after_environment_fallback() -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock(
        side_effect=[
            ClientError("file credentials expired"),
            ClientError("environment credentials expired"),
        ]
    )

    with pytest.raises(ClientError, match="environment credentials expired"):
        service.evaluate_refresh()

    assert service.refresh_credentials.call_count == 2
    config_manager.eval_retry.assert_called_once_with()


def test_evaluate_refresh_stops_after_maximum_attempts() -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock(side_effect=ClientError("credentials expired"))

    with pytest.raises(ClientError, match="credentials expired"):
        service.evaluate_refresh()

    assert service.refresh_credentials.call_count == get_client_config().max_refresh_attempts
    config_manager.eval_retry.assert_called_once_with()


def test_evaluate_refresh_uses_configured_maximum_attempts(monkeypatch) -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    configured_client = Mock(max_refresh_attempts=1)
    monkeypatch.setattr(refresh_module, "get_client_config", Mock(return_value=configured_client))
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock(side_effect=ClientError("credentials expired"))

    with pytest.raises(ClientError, match="credentials expired"):
        service.evaluate_refresh()

    service.refresh_credentials.assert_called_once_with()
    config_manager.eval_retry.assert_not_called()


def test_evaluate_refresh_rejects_non_positive_maximum_attempts(monkeypatch) -> None:
    config_manager = Mock()
    configured_client = Mock(max_refresh_attempts=0)
    monkeypatch.setattr(refresh_module, "get_client_config", Mock(return_value=configured_client))
    service = TokenRefreshService(config_manager, Mock(), Mock())
    service.refresh_credentials = Mock()

    with pytest.raises(ClientError, match="max_refresh_attempts must be at least 1"):
        service.evaluate_refresh()

    service.refresh_credentials.assert_not_called()


def test_refresh_uses_request_transport(monkeypatch) -> None:
    config_manager = Mock()
    config_manager.get_credentials_and_config.return_value = {
        ConfigurationVars.DHCORE_CLIENT_ID.value: "client",
        ConfigurationVars.OAUTH2_TOKEN_ENDPOINT.value: "https://issuer.example/token",
        CredentialsVars.DHCORE_REFRESH_TOKEN.value: "refresh",
    }
    auth_session = Mock()
    auth_session.auth_type = AuthType.OAUTH2.value
    auth_session.is_refreshable.return_value = True
    response = Mock()
    response.json.return_value = {"access_token": "new"}
    transport = Mock()
    transport.execute.return_value = response

    service = TokenRefreshService(config_manager, auth_session, transport)

    service.refresh_credentials()

    transport.execute.assert_called_once()
    request = transport.execute.call_args.args[0]
    assert isinstance(request, BERequest)
    assert request.method == "POST"
    assert request.api == "https://issuer.example/token"
    assert request.operation == OpsType.AUTH_REFRESH.value
    assert request.data["grant_type"] == get_client_config().oauth2_grant_type
    assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert request.authenticate is False
    assert transport.execute.call_args.kwargs == {}
    config_manager.save_refreshed_credentials.assert_called_once_with({"access_token": "new"})


def test_refresh_maps_backend_error_response_to_sdk_error() -> None:
    config_manager = Mock()
    config_manager.get_credentials_and_config.return_value = {
        ConfigurationVars.DHCORE_CLIENT_ID.value: "client",
        ConfigurationVars.OAUTH2_TOKEN_ENDPOINT.value: "https://issuer.example/token",
        CredentialsVars.DHCORE_REFRESH_TOKEN.value: "already-used",
    }
    auth_session = Mock()
    auth_session.auth_type = AuthType.OAUTH2.value
    auth_session.is_refreshable.return_value = True
    response = Response()
    response.status_code = 400
    response.url = "https://issuer.example/token"
    response.headers = {}
    response._content = b"Refresh token does not exist"
    transport = Mock()
    transport.execute.return_value = response

    service = TokenRefreshService(config_manager, auth_session, transport)

    with pytest.raises(BadRequestError, match="Refresh token does not exist"):
        service.refresh_credentials()


def test_refresh_discovery_requires_token_endpoint() -> None:
    config_manager = Mock()
    config_manager.configuration = {ConfigurationVars.DHCORE_ISSUER.value: "https://issuer.example"}
    auth_session = Mock()
    auth_session.auth_type = AuthType.OAUTH2.value
    auth_session.is_refreshable.return_value = True
    response = Mock()
    response.json.return_value = {}
    transport = Mock()
    transport.execute.return_value = response
    service = TokenRefreshService(config_manager, auth_session, transport)

    with pytest.raises(ClientError, match="Token endpoint not set"):
        service._get_refresh_endpoint()
