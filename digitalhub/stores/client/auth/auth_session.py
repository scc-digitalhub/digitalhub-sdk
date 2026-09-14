# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.auth.credential_session import CredentialSession
from digitalhub.stores.client.auth.enums import CredentialSource, CredentialsVars
from digitalhub.stores.client.common.enums import AuthType
from digitalhub.stores.client.common.utils import set_basic_auth, set_bearer_token


class AuthSession:
    """Expose authentication behaviour for the active credential session."""

    def __init__(self, credential_session: CredentialSession) -> None:
        self._credential_session = credential_session

    def _eval_auth_type(self) -> str:
        """Determine the authentication type from the active credentials."""
        creds = self.credentials

        if creds[CredentialsVars.DHCORE_PERSONAL_ACCESS_TOKEN.value] is not None:
            return AuthType.EXCHANGE.value

        if creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value] is not None:
            if creds[CredentialsVars.DHCORE_REFRESH_TOKEN.value] is not None:
                return AuthType.OAUTH2.value
            return AuthType.ACCESS_TOKEN.value

        if (
            creds[CredentialsVars.DHCORE_USER.value] is not None
            and creds[CredentialsVars.DHCORE_PASSWORD.value] is not None
        ):
            return AuthType.BASIC.value

        return AuthType.NO_AUTH.value

    def is_refreshable(self) -> bool:
        """Return whether the active authentication supports token refresh."""
        return self.auth_type in [AuthType.OAUTH2.value, AuthType.EXCHANGE.value]

    def get_auth_parameters(self, kwargs: dict | None = None) -> dict:
        """Add authentication parameters for the active credentials."""
        if kwargs is None:
            kwargs = {}

        creds = self.credentials
        match self.auth_type:
            case AuthType.EXCHANGE.value | AuthType.OAUTH2.value | AuthType.ACCESS_TOKEN.value:
                kwargs = set_bearer_token(creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value], **kwargs)
            case AuthType.BASIC.value:
                kwargs = set_basic_auth(
                    creds[CredentialsVars.DHCORE_USER.value],
                    creds[CredentialsVars.DHCORE_PASSWORD.value],
                    **kwargs,
                )
            case _:
                pass
        return kwargs

    @property
    def auth_type(self) -> str:
        return self._eval_auth_type()

    @property
    def credentials(self) -> dict:
        return self._credential_session.credentials

    @property
    def source(self) -> CredentialSource:
        return self._credential_session.source
