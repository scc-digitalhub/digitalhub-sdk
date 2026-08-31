from unittest.mock import Mock

import pytest

from digitalhub.stores.client.auth.config_manager import ConfigManager
from digitalhub.utils.exceptions import ClientError


def test_initialization_does_not_write_configuration(monkeypatch) -> None:
    monkeypatch.setattr(ConfigManager, "_read_current_profile", Mock(return_value="default"))
    monkeypatch.setattr(ConfigManager, "load_configuration", Mock(return_value={"DHCORE_ENDPOINT": "https://example.test"}))
    monkeypatch.setattr(ConfigManager, "load_credentials", Mock(return_value={}))
    export_to_ini = Mock()
    export_to_env = Mock()
    monkeypatch.setattr(ConfigManager, "export_to_ini", export_to_ini)
    monkeypatch.setattr(ConfigManager, "export_to_env", export_to_env)

    manager = ConfigManager()

    assert manager.in_memory is False
    export_to_ini.assert_not_called()
    export_to_env.assert_not_called()


def test_save_credentials_persists_and_reloads() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._in_memory = False
    manager.export_to_ini = Mock()
    manager.export_to_env = Mock()
    manager.reload_credentials = Mock()
    manager.load_to_env = Mock()
    credentials = {"dhcore_access_token": "new"}

    manager.save_credentials(credentials)

    manager.export_to_ini.assert_called_once_with(credentials)
    manager.export_to_env.assert_called_once_with(credentials)
    manager.reload_credentials.assert_called_once_with()
    manager.load_to_env.assert_called_once_with()


def test_save_credentials_updates_in_memory_without_persistence() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._in_memory = True
    manager._credentials = {}
    manager.export_to_ini = Mock()
    manager.export_to_env = Mock()

    manager.save_credentials({"dhcore_access_token": "new"})

    assert manager.credentials == {"DHCORE_ACCESS_TOKEN": "new"}
    manager.export_to_ini.assert_not_called()
    manager.export_to_env.assert_not_called()


def test_save_credentials_falls_back_to_memory_when_file_is_unwritable() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._in_memory = False
    manager._credentials = {}
    manager.export_to_ini = Mock(side_effect=ClientError("unwritable"))
    manager.export_to_env = Mock()

    with pytest.warns(UserWarning, match="stored in memory"):
        manager.save_credentials({"dhcore_access_token": "new"})

    assert manager.in_memory is True
    assert manager.credentials == {"DHCORE_ACCESS_TOKEN": "new"}
    manager.export_to_env.assert_not_called()
