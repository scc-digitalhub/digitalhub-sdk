# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

import digitalhub.stores.session as session_module
from digitalhub.stores.client.common.config import (
    ClientConfig,
    _get_config_file_path,
    get_client_config,
    set_client_config,
)
from digitalhub.stores.client.common.enums import ConfigurationVars
from digitalhub.stores.client.common.utils import sanitize_endpoint
from digitalhub.stores.client.factory import get_client
from digitalhub.stores.session import Session


@pytest.fixture(autouse=True)
def restore_client_config():
    original_config = get_client_config()
    yield
    set_client_config(original_config)


def test_set_client_config_reconfigures_the_session(monkeypatch) -> None:
    transport = Mock()
    session = Session(transport=transport, identity=Mock())
    monkeypatch.setattr(session_module, "_session", session)
    original_client = get_client()
    config = ClientConfig(http_timeout=120)

    set_client_config(config)
    client = get_client()

    assert get_client_config() is config
    assert session.config is config
    assert client is not original_client
    assert client._config is config
    assert client._transport is transport


def test_dh_config_set_after_import_applies_to_the_session(monkeypatch, tmp_path) -> None:
    # The configuration was built when digitalhub was imported, so DH_CONFIG
    # set afterwards, for example in a notebook, was ignored, while the other
    # variables were read at use.
    config_path = tmp_path / "custom.ini"
    monkeypatch.setattr(session_module, "_session", None)
    monkeypatch.setenv(ConfigurationVars.DH_CONFIG.value, str(config_path))

    assert get_client_config().config_ini_path == config_path


def test_client_config_rejects_non_positive_refresh_attempts() -> None:
    with pytest.raises(ValueError, match="max_refresh_attempts must be at least 1"):
        ClientConfig(max_refresh_attempts=0)


def test_config_file_path_uses_configuration_var(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "custom.ini"
    monkeypatch.setenv(ConfigurationVars.DH_CONFIG.value, str(config_path))

    assert _get_config_file_path() == config_path


def test_sanitize_endpoint_strips_whitespace_before_validation() -> None:
    assert sanitize_endpoint(" https://example.test/ ") == "https://example.test"
