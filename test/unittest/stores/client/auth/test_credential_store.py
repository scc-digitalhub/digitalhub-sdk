from unittest.mock import Mock

import digitalhub.stores.client.auth.credential_store as credential_store_module
from digitalhub.stores.client.auth.credential_store import CredentialStore
from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars


def test_loads_configuration_and_credentials_with_file_precedence(monkeypatch) -> None:
    store = CredentialStore("default")
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
        CredentialStore,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(
        CredentialStore,
        "_read_file",
        staticmethod(lambda variables, profile: {key: file_values.get(key) for key in variables}),
    )

    configuration = store.load_configuration()
    credentials = store.load_credentials()

    assert configuration[ConfigurationVars.DHCORE_ENDPOINT.value] == "https://file.example.test"
    assert credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "file-access"
    assert credentials[CredentialsVars.DHCORE_USER.value] == "env-user"


def test_loads_credentials_from_environment_without_reading_file(monkeypatch) -> None:
    store = CredentialStore("default")
    env_values = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access"}

    monkeypatch.setattr(
        CredentialStore,
        "_read_env",
        staticmethod(lambda variables: {key: env_values.get(key) for key in variables}),
    )
    monkeypatch.setattr(
        CredentialStore,
        "_read_file",
        staticmethod(lambda variables, profile: (_ for _ in ()).throw(AssertionError("file was read"))),
    )

    credentials = store.load_credentials_from_env()

    assert credentials[CredentialsVars.DHCORE_ACCESS_TOKEN.value] == "env-access"


def test_persists_credentials_to_the_active_profile(monkeypatch) -> None:
    store = CredentialStore("default")
    write_file = Mock()
    monkeypatch.setattr(credential_store_module, "write_file", write_file)

    credentials = {"dhcore_access_token": "new-access"}
    store.export_to_ini(credentials)

    write_file.assert_called_once_with(credentials, "default")


def test_delegates_dotenv_operations(monkeypatch) -> None:
    store = CredentialStore("default")
    write_dotenv = Mock()
    load_dotenv_file = Mock()
    monkeypatch.setattr(credential_store_module, "write_dotenv", write_dotenv)
    monkeypatch.setattr(credential_store_module, "load_dotenv_file", load_dotenv_file)

    credentials = {"dhcore_access_token": "new-access"}
    store.export_to_env(credentials)
    store.load_to_env()

    write_dotenv.assert_called_once_with(credentials)
    load_dotenv_file.assert_called_once_with()
