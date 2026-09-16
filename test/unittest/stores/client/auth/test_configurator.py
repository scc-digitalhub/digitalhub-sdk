# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.common.enums import AuthType
from digitalhub.stores.client.http.request import BackendReq


def test_constructor_defers_exchange_bootstrap(monkeypatch) -> None:
    config_manager = Mock()
    config_manager.credential_session = object()
    auth_session = Mock(auth_type=AuthType.EXCHANGE.value)
    refresh_service = Mock()

    monkeypatch.setattr(
        "digitalhub.stores.client.auth.client_configurator.ConfigManager",
        Mock(return_value=config_manager),
    )
    monkeypatch.setattr(
        "digitalhub.stores.client.auth.client_configurator.AuthSession",
        Mock(return_value=auth_session),
    )
    monkeypatch.setattr(
        "digitalhub.stores.client.auth.client_configurator.TokenRefreshService",
        Mock(return_value=refresh_service),
    )

    configurator = ClientConfigurator(Mock())

    refresh_service.evaluate_refresh.assert_not_called()
    assert configurator._exchange_bootstrapped is False


def test_authenticate_bootstraps_exchange_once() -> None:
    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator._auth_session = Mock(auth_type=AuthType.EXCHANGE.value)
    configurator._exchange_bootstrapped = False
    configurator.evaluate_refresh = Mock()
    request = BackendReq(method="GET", api="/resource")

    configurator.authenticate(request)
    configurator.authenticate(request)

    configurator.evaluate_refresh.assert_called_once_with()
    assert configurator._auth_session.authenticate.call_count == 2


def test_set_current_profile_resets_exchange_bootstrap() -> None:
    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator._config_manager = Mock()
    configurator._exchange_bootstrapped = True

    configurator.set_current_profile("other")

    configurator._config_manager.set_current_profile.assert_called_once_with("other")
    assert configurator._exchange_bootstrapped is False


def test_get_credentials_and_config_is_a_pure_getter() -> None:
    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator._config_manager = Mock()
    configurator._config_manager.get_credentials_and_config.return_value = {"access_token": "current"}

    result = configurator.get_credentials_and_config()

    assert result == {"access_token": "current"}
    configurator._config_manager.get_credentials_and_config.assert_called_once_with()
