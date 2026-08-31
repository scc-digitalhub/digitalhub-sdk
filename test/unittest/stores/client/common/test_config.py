from types import SimpleNamespace

import pytest

import digitalhub.stores.client.base.factory as factory_module
from digitalhub.stores.client.auth import file_module
from digitalhub.stores.client.builders.api import ClientApiBuilder
from digitalhub.stores.client.common.config import ClientConfig, get_client_config, set_client_config
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
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
        ApiCategories.BASE.value,
        BackendOperations.LIST.value,
        entity_type="project",
    )
    context_api = api_builder.build_api(
        ApiCategories.CONTEXT.value,
        BackendOperations.LIST.value,
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
