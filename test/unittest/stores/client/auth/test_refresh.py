from unittest.mock import Mock

import pytest

import digitalhub.stores.client.auth.refresh as refresh_module
from digitalhub.stores.client.auth.refresh import TokenRefreshService
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.utils.exceptions import ClientError


def test_evaluate_refresh_propagates_unexpected_errors() -> None:
    config_manager = Mock()
    service = TokenRefreshService(config_manager, Mock())
    service.refresh_credentials = Mock(side_effect=RuntimeError("internal failure"))

    with pytest.raises(RuntimeError, match="internal failure"):
        service.evaluate_refresh()

    config_manager.eval_retry.assert_not_called()


def test_evaluate_refresh_retries_expected_credential_errors() -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    service = TokenRefreshService(config_manager, Mock())
    service.refresh_credentials = Mock(side_effect=[ClientError("invalid credentials"), None])

    assert service.evaluate_refresh() is True
    assert service.refresh_credentials.call_count == 2
    config_manager.eval_retry.assert_called_once_with()


def test_evaluate_refresh_propagates_error_after_environment_fallback() -> None:
    config_manager = Mock()
    config_manager.eval_retry.return_value = True
    service = TokenRefreshService(config_manager, Mock())
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
    service = TokenRefreshService(config_manager, Mock())
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
    service = TokenRefreshService(config_manager, Mock())
    service.refresh_credentials = Mock(side_effect=ClientError("credentials expired"))

    with pytest.raises(ClientError, match="credentials expired"):
        service.evaluate_refresh()

    service.refresh_credentials.assert_called_once_with()
    config_manager.eval_retry.assert_not_called()


def test_export_new_credentials_delegates_persistence() -> None:
    config_manager = Mock()
    service = TokenRefreshService(config_manager, Mock())

    service._export_new_creds({"access_token": "new"})

    config_manager.save_credentials.assert_called_once_with({"dhcore_access_token": "new"})


def test_export_new_credentials_preserves_all_refreshed_credentials() -> None:
    config_manager = Mock()
    service = TokenRefreshService(config_manager, Mock())

    service._export_new_creds(
        {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "aws_access_key_id": "new-s3-access",
            "db_password": "new-db-password",
        }
    )

    config_manager.save_credentials.assert_called_once_with(
        {
            "dhcore_access_token": "new-access",
            "dhcore_refresh_token": "new-refresh",
            "aws_access_key_id": "new-s3-access",
            "db_password": "new-db-password",
        }
    )
