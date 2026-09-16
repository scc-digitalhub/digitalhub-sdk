# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.stores.client.auth.credential_session import CredentialSession
from digitalhub.stores.client.common.enums import CredentialSource, CredentialsVars


def test_file_credentials_are_active_initially() -> None:
    credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"}

    session = CredentialSession(credentials)

    assert session.credentials == credentials
    assert session.source is CredentialSource.FILE


def test_retry_switches_to_environment_when_file_credentials_are_unchanged() -> None:
    file_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"}
    env_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access"}
    session = CredentialSession(file_credentials)

    assert session.retry(file_credentials, env_credentials) is True
    assert session.credentials == env_credentials
    assert session.source is CredentialSource.ENV


def test_retry_reloads_changed_file_credentials() -> None:
    current_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "old-file-access"}
    file_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "new-file-access"}
    env_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access"}
    session = CredentialSession(current_credentials)

    assert session.retry(file_credentials, env_credentials) is True
    assert session.credentials == file_credentials
    assert session.source is CredentialSource.FILE


def test_retry_stops_after_environment_is_active() -> None:
    file_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "file-access"}
    env_credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "env-access"}
    session = CredentialSession(file_credentials)
    session.use_environment(env_credentials)

    assert session.retry(file_credentials, env_credentials) is False
    assert session.credentials == env_credentials
    assert session.source is CredentialSource.ENV


def test_update_changes_active_credentials_without_changing_source() -> None:
    credentials = {CredentialsVars.DHCORE_ACCESS_TOKEN.value: "access-token"}
    session = CredentialSession(credentials)
    session.use_environment(credentials)

    session.update({CredentialsVars.DHCORE_REFRESH_TOKEN.value: "refresh-token"})

    assert session.credentials == {
        CredentialsVars.DHCORE_ACCESS_TOKEN.value: "access-token",
        CredentialsVars.DHCORE_REFRESH_TOKEN.value: "refresh-token",
    }
    assert session.source is CredentialSource.ENV
