from unittest.mock import Mock

import pytest
from requests.exceptions import HTTPError
from requests.exceptions import Timeout as RequestsTimeout

import digitalhub.stores.client.auth.client_configurator as configurator_module
import digitalhub.stores.client.http.transport as transport_module
from digitalhub.stores.client.auth.client_configurator import ClientConfigurator


def test_get_credentials_normalizes_transport_timeout(monkeypatch) -> None:
    transport_error = RequestsTimeout()
    monkeypatch.setattr(transport_module, "requests_request", Mock(side_effect=transport_error))

    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator.get_endpoint = Mock(return_value="https://example.test")
    configurator.get_auth_parameters = Mock(return_value={})

    with pytest.raises(TimeoutError, match="Request to DHCore backend timed out.") as exc_info:
        configurator.get_credentials_and_config()

    assert exc_info.value.__cause__ is transport_error


def test_get_credentials_returns_updated_config_after_refresh(monkeypatch) -> None:
    unauthorized_response = Mock(status_code=401)
    unauthorized_response.raise_for_status.side_effect = HTTPError()
    successful_response = Mock(status_code=200)
    request = Mock(side_effect=[unauthorized_response, successful_response])
    monkeypatch.setattr(configurator_module, "request", request)

    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator._config_manager = Mock()
    configurator._config_manager.get_credentials_and_config.return_value = {"access_token": "refreshed"}
    configurator.get_endpoint = Mock(return_value="https://example.test")
    configurator.get_auth_parameters = Mock(side_effect=[{"headers": {"Authorization": "old"}}, {"headers": {"Authorization": "new"}}])
    configurator.evaluate_refresh = Mock(return_value=True)

    result = configurator.get_credentials_and_config()

    assert result == {"access_token": "refreshed"}
    successful_response.raise_for_status.assert_called_once_with()
    configurator._config_manager.get_credentials_and_config.assert_called_once_with()
