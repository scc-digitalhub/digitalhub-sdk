from unittest.mock import Mock

import pytest

from digitalhub.stores.client.auth.refresh import TokenRefreshService
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


def test_export_new_credentials_delegates_persistence() -> None:
    config_manager = Mock()
    service = TokenRefreshService(config_manager, Mock())

    service._export_new_creds({"access_token": "new"})

    config_manager.save_credentials.assert_called_once_with({"dhcore_access_token": "new"})
