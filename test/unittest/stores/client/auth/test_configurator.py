# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import threading
from unittest.mock import Mock

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.client.common.enums import AuthType, ConfigurationVars, CredentialsVars
from digitalhub.stores.client.common.utils import with_bearer_token
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.generic_utils import list_enum


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


def test_configurator_passes_its_configuration_to_credentials_and_refresh(monkeypatch) -> None:
    config = ClientConfig(max_refresh_attempts=1)
    transport = Mock()
    config_manager_factory = Mock()
    refresh_service_factory = Mock()
    module = "digitalhub.stores.client.auth.client_configurator"
    monkeypatch.setattr(f"{module}.ConfigManager", config_manager_factory)
    monkeypatch.setattr(f"{module}.AuthSession", Mock())
    monkeypatch.setattr(f"{module}.TokenRefreshService", refresh_service_factory)

    ClientConfigurator(transport, config)

    config_manager_factory.assert_called_once_with(config)
    assert refresh_service_factory.call_args.args[2:] == (transport, config)


def _configurator_with_token(token: str) -> ClientConfigurator:
    configurator = ClientConfigurator.__new__(ClientConfigurator)
    configurator._refresh_lock = threading.Lock()
    configurator._auth_session = Mock()
    configurator._auth_session.authenticate.side_effect = lambda request: with_bearer_token(request, token)
    configurator._token_refresh_service = Mock()
    return configurator


def test_invalidate_refreshes_credentials_and_reports_whether_to_retry() -> None:
    configurator = _configurator_with_token("old")
    configurator._token_refresh_service.evaluate_refresh.return_value = False
    rejected = with_bearer_token(BackendReq(method="GET", api="/resource"), "old")

    assert configurator.invalidate(rejected) is False
    configurator._token_refresh_service.evaluate_refresh.assert_called_once_with()


def test_invalidate_does_not_refresh_credentials_replaced_after_the_request() -> None:
    # Another thread refreshed while the request was in flight: refreshing
    # again would send a refresh token Core has already consumed.
    configurator = _configurator_with_token("new")
    rejected = with_bearer_token(BackendReq(method="GET", api="/resource"), "old")

    assert configurator.invalidate(rejected) is True
    configurator._token_refresh_service.evaluate_refresh.assert_not_called()


def _profile(tmp_path, monkeypatch, extra: str = "") -> ClientConfig:
    for variable in [*list_enum(ConfigurationVars), *list_enum(CredentialsVars)]:
        monkeypatch.delenv(variable, raising=False)
    ini = tmp_path / ".dhcore.ini"
    ini.write_text(
        "[DEFAULT]\ncurrent_environment = test\n\n[test]\n"
        f"dhcore_endpoint = http://core.test\ndhcore_access_token = A0\n{extra}"
    )
    return ClientConfig(config_ini_path=ini)


def test_proxy_comes_from_dhcore_proxy(monkeypatch, tmp_path) -> None:
    config = _profile(tmp_path, monkeypatch)
    assert ClientConfigurator(Mock(), config).get_proxy() is None

    monkeypatch.setenv("DHCORE_PROXY", "https://proxy.test/")
    assert ClientConfigurator(Mock(), config).get_proxy() == "https://proxy.test"


def test_proxy_published_by_core_is_read_from_the_profile(monkeypatch, tmp_path) -> None:
    config = _profile(tmp_path, monkeypatch, "dhcore_proxy = https://proxy.test\n")

    assert ClientConfigurator(Mock(), config).get_proxy() == "https://proxy.test"
