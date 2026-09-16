# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.stores.client.auth.credential_store as credential_store_module
from digitalhub.stores.client.auth.config_manager import ConfigManager
from digitalhub.stores.client.auth.credential_session import CredentialSession
from digitalhub.stores.client.common.enums import ConfigurationVars, CredentialsVars
from digitalhub.utils.exceptions import ClientError


def test_configuration_and_credentials_use_file_precedence(monkeypatch) -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._current_profile = "default"
    manager._credential_store = credential_store_module.CredentialStore("default")
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
        credential_store_module.CredentialStore,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(
        credential_store_module.CredentialStore,
        "_read_file",
        staticmethod(lambda variables, profile: {key: file_values.get(key) for key in variables}),
    )

    configuration = manager.load_configuration()
    credentials = manager.load_credentials()

    assert configuration[ConfigurationVars.DHCORE_ENDPOINT.value] == "https://file.example.test"
    assert credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "file-access"
    assert credentials[CredentialsVars.DHCORE_USER.value] == "env-user"


def test_eval_retry_stops_reading_file_after_environment_fallback(monkeypatch) -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._current_profile = "default"
    manager._credential_store = credential_store_module.CredentialStore("default")
    manager._credential_session = CredentialSession({CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"})
    file_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"}
    manager.load_credentials = Mock(return_value=file_credentials)
    env_values = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access"}

    monkeypatch.setattr(
        credential_store_module.CredentialStore,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(
        credential_store_module.CredentialStore,
        "_read_file",
        staticmethod(Mock(side_effect=AssertionError("file must not be read after fallback"))),
    )

    assert manager.eval_retry() is True
    assert manager.credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "env-access"
    manager.load_credentials.side_effect = AssertionError("file must not be checked again")

    assert manager.eval_retry() is False


def test_save_credentials_after_environment_fallback_keeps_memory_state() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._credential_store = credential_store_module.CredentialStore("default")
    manager._in_memory = False
    manager._credential_session = CredentialSession(
        {
            CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access",
            CredentialsVars.S3_ACCESS_KEY_ID.value: "old-s3-access",
        }
    )
    manager._credential_session.use_environment(manager.credentials)
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


def test_save_refreshed_credentials_normalizes_backend_keys_without_mutating_input() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager.save_credentials = Mock()
    refreshed_credentials = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "token_endpoint": "https://issuer.example/token",
        "aws_access_key_id": "new-s3-access",
    }

    manager.save_refreshed_credentials(refreshed_credentials)

    manager.save_credentials.assert_called_once_with(
        {
            "dhcore_access_token": "new-access",
            "dhcore_refresh_token": "new-refresh",
            "oauth2_token_endpoint": "https://issuer.example/token",
            "aws_access_key_id": "new-s3-access",
        }
    )
    assert refreshed_credentials == {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "token_endpoint": "https://issuer.example/token",
        "aws_access_key_id": "new-s3-access",
    }


def test_initialization_does_not_write_configuration(monkeypatch) -> None:
    monkeypatch.setattr(ConfigManager, "_read_current_profile", Mock(return_value="default"))
    monkeypatch.setattr(
        ConfigManager, "load_configuration", Mock(return_value={"DHCORE_ENDPOINT": "https://example.test"})
    )
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
    manager._credential_session = CredentialSession({})
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
    manager._credential_session = CredentialSession({})
    manager.export_to_ini = Mock()
    manager.export_to_env = Mock()

    manager.save_credentials({"dhcore_access_token": "new"})

    assert manager.credentials == {"DHCORE_ACCESS_TOKEN": "new"}
    manager.export_to_ini.assert_not_called()
    manager.export_to_env.assert_not_called()


def test_save_credentials_falls_back_to_memory_when_file_is_unwritable() -> None:
    manager = ConfigManager.__new__(ConfigManager)
    manager._in_memory = False
    manager._credential_session = CredentialSession({})
    manager.export_to_ini = Mock(side_effect=ClientError("unwritable"))
    manager.export_to_env = Mock()

    manager.save_credentials({"dhcore_access_token": "new"})

    assert manager.in_memory is True
    assert manager.credentials == {"DHCORE_ACCESS_TOKEN": "new"}
    manager.export_to_env.assert_not_called()
