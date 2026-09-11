from unittest.mock import Mock

from digitalhub.stores.client.auth.config_manager import ConfigManager
from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars
from digitalhub.utils.exceptions import ClientError


def test_configuration_and_credentials_use_their_declared_precedence(monkeypatch) -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._current_profile = "default"
    env_values = {
        ConfigurationVars.DHCORE_ENDPOINT.value: "https://env.example.test",
        CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access",
        CredentialsVars.DHCORE_USER.value: "env-user",
    }
    file_values = {
        ConfigurationVars.DHCORE_ENDPOINT.value: "https://file.example.test",
        CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access",
    }

    monkeypatch.setattr(
        ConfigManager,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(
        ConfigManager,
        "_read_file",
        staticmethod(lambda variables, profile: {key: file_values.get(key) for key in variables}),
    )

    configuration = manager.load_configuration()
    credentials = manager.load_credentials()

    assert configuration[ConfigurationVars.DHCORE_ENDPOINT.value] == "https://env.example.test"
    assert credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "file-access"
    assert credentials[CredentialsVars.DHCORE_USER.value] == "env-user"


def test_reload_credentials_from_env_does_not_read_file(monkeypatch) -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._current_profile = "default"
    env_values = {
        CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access",
        CredentialsVars.S3_ACCESS_KEY_ID.value: "env-s3-access",
    }
    read_file = Mock(side_effect=AssertionError("file must not be read"))

    monkeypatch.setattr(
        ConfigManager,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(ConfigManager, "_read_file", staticmethod(read_file))

    manager.reload_credentials_from_env()

    assert manager.credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "env-access"
    assert manager.credentials[CredentialsVars.S3_ACCESS_KEY_ID.value] == "env-s3-access"
    read_file.assert_not_called()


def test_eval_retry_stops_reading_file_after_environment_fallback(monkeypatch) -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._current_profile = "default"
    manager._credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"}
    manager._reloaded_from_env = False
    file_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"}
    manager.load_credentials = Mock(return_value=file_credentials)
    env_values = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access"}

    monkeypatch.setattr(
        ConfigManager,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(
        ConfigManager,
        "_read_file",
        staticmethod(Mock(side_effect=AssertionError("file must not be read after fallback"))),
    )

    assert manager.eval_retry() is True
    assert manager.credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "env-access"
    manager.load_credentials.side_effect = AssertionError("file must not be checked again")

    assert manager.eval_retry() is False


def test_save_credentials_after_environment_fallback_keeps_memory_state() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._in_memory = False
    manager._reloaded_from_env = True
    manager._credentials = {
        CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access",
        CredentialsVars.S3_ACCESS_KEY_ID.value: "old-s3-access",
    }
    manager.export_to_ini = Mock()
    manager.export_to_env = Mock()
    manager.reload_credentials = Mock(side_effect=AssertionError("file must not be reloaded"))

    manager.save_credentials(
        {
            "dhcore_access_token": "new-access",
            "aws_access_key_id": "new-s3-access",
        }
    )

    assert manager.credentials == {
        CredentialsVars.DHCORE_ACCESS_TOKEN.value: "new-access",
        CredentialsVars.S3_ACCESS_KEY_ID.value: "new-s3-access",
    }
    manager.reload_credentials.assert_not_called()


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
    manager._reloaded_from_env = False
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

    manager.save_credentials({"dhcore_access_token": "new"})

    assert manager.in_memory is True
    assert manager.credentials == {"DHCORE_ACCESS_TOKEN": "new"}
    manager.export_to_env.assert_not_called()
