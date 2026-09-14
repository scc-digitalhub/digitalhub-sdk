from unittest.mock import Mock

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator


def test_get_credentials_and_config_is_a_pure_getter() -> None:
    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator._config_manager = Mock()
    configurator._config_manager.get_credentials_and_config.return_value = {"access_token": "current"}

    result = configurator.get_credentials_and_config()

    assert result == {"access_token": "current"}
    configurator._config_manager.get_credentials_and_config.assert_called_once_with()
