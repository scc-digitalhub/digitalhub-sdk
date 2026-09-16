# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest

import digitalhub.stores.client.factory as factory_module
from digitalhub.stores.client.auth import file_module
from digitalhub.stores.client.common.config import (
    ClientConfig,
    _get_config_file_path,
    get_client_config,
    set_client_config,
)
from digitalhub.stores.client.common.enums import ApiType, BEOps, ConfigurationVars
from digitalhub.stores.client.common.utils import sanitize_endpoint
from digitalhub.stores.client.compiler.apis.api import ClientApiBuilder
from digitalhub.stores.client.http.response import ResponseProcessor


@pytest.fixture(autouse=True)
def restore_client_config():
    original_config = get_client_config()
    yield
    set_client_config(original_config)


def test_set_client_config_updates_imported_dependencies(monkeypatch, tmp_path) -> None:
    old_directory = tmp_path / "old"
    old_directory.mkdir()
    monkeypatch.setattr(file_module, "DOTENV_FILE", old_directory / ".env", raising=False)

    config_directory = tmp_path / "current"
    config_directory.mkdir()
    set_client_config(
        ClientConfig(
            config_ini_path=config_directory / "config.ini",
            api_base="/custom/base",
            api_context="/custom/context",
            min_api_level=30,
            max_api_level=31,
            lib_version=30,
        )
    )

    file_module.write_dotenv({"access_token": "token"})
    api_builder = ClientApiBuilder()
    base_api = api_builder.build_api(
        ApiType.BASE,
        BEOps.LIST,
        entity_type="project",
    )
    context_api = api_builder.build_api(
        ApiType.CONTEXT,
        BEOps.LIST,
        project="project",
        entity_type="function",
    )
    ResponseProcessor()._check_api_version(SimpleNamespace(headers={"X-Api-Level": "30"}))

    assert (config_directory / ".env").exists()
    assert not (old_directory / ".env").exists()
    assert base_api == "/custom/base/projects"
    assert context_api == "/custom/context/project/functions"


def test_set_client_config_invalidates_default_client(monkeypatch) -> None:
    monkeypatch.setattr(factory_module, "Client", lambda: object())
    factory_module.client_factory._client = None
    original_client = factory_module.get_client()

    set_client_config(ClientConfig(http_timeout=120))

    assert factory_module.get_client() is not original_client


def test_client_config_rejects_non_positive_refresh_attempts() -> None:
    with pytest.raises(ValueError, match="max_refresh_attempts must be at least 1"):
        ClientConfig(max_refresh_attempts=0)


def test_config_file_path_uses_configuration_var(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "custom.ini"
    monkeypatch.setenv(ConfigurationVars.DH_CONFIG.value, str(config_path))

    assert _get_config_file_path() == config_path


def test_sanitize_endpoint_strips_whitespace_before_validation() -> None:
    assert sanitize_endpoint(" https://example.test/ ") == "https://example.test"
