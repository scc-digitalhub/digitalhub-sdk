from digitalhub.stores.client.auth.auth_session import AuthSession
from digitalhub.stores.client.auth.credential_session import CredentialSession
from digitalhub.stores.client.auth.enums import CredentialsVars
from digitalhub.stores.client.common.enums import AuthType


def _credentials(**values: str | None) -> dict[str, str | None]:
    credentials = {variable.value: None for variable in CredentialsVars}
    credentials.update(values)
    return credentials


def test_auth_session_derives_auth_type_from_its_credential_session() -> None:
    credential_session = CredentialSession(
        _credentials(
            DHCORE_ACCESS_TOKEN="file-access",
            DHCORE_REFRESH_TOKEN="file-refresh",
        )
    )
    auth_session = AuthSession(credential_session)

    assert auth_session.credentials is credential_session.credentials
    assert auth_session.source is credential_session.source
    assert auth_session.auth_type == AuthType.OAUTH2.value

    credential_session.use_environment(_credentials(DHCORE_ACCESS_TOKEN="env-access"))

    assert auth_session.credentials is credential_session.credentials
    assert auth_session.source is credential_session.source
    assert auth_session.auth_type == AuthType.ACCESS_TOKEN.value
    assert auth_session.is_refreshable() is False


def test_auth_session_uses_bearer_auth_for_personal_access_tokens() -> None:
    auth_session = AuthSession(
        CredentialSession(
            _credentials(
                DHCORE_PERSONAL_ACCESS_TOKEN="personal-access-token",
                DHCORE_ACCESS_TOKEN="access-token",
            )
        )
    )

    assert auth_session.auth_type == AuthType.EXCHANGE.value
    assert auth_session.is_refreshable() is True
    assert auth_session.get_auth_parameters() == {"headers": {"Authorization": "Bearer access-token"}}


def test_auth_session_uses_basic_auth_for_user_credentials() -> None:
    auth_session = AuthSession(
        CredentialSession(
            _credentials(
                DHCORE_USER="user",
                DHCORE_PASSWORD="password",
            )
        )
    )

    assert auth_session.auth_type == AuthType.BASIC.value
    assert auth_session.is_refreshable() is False
    assert auth_session.get_auth_parameters() == {"auth": ("user", "password")}


def test_auth_session_keeps_request_parameters_for_no_auth() -> None:
    auth_session = AuthSession(CredentialSession(_credentials()))
    kwargs = {"params": {"page": 1}}

    assert auth_session.auth_type == AuthType.NO_AUTH.value
    assert auth_session.is_refreshable() is False
    assert auth_session.get_auth_parameters(kwargs) is kwargs
