# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import replace

from digitalhub.stores.client.auth.credential_session import CredentialSession
from digitalhub.stores.client.common.enums import AuthType, CredentialSource, CredentialsVars
from digitalhub.stores.client.common.utils import with_basic_auth, with_bearer_token
from digitalhub.stores.client.http.request import BackendReq


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

    def authenticate(self, backend_request: BackendReq) -> BackendReq:
        """Return an authenticated copy of a backend request."""
        creds = self.credentials
        match self.auth_type:
            case AuthType.EXCHANGE.value | AuthType.OAUTH2.value | AuthType.ACCESS_TOKEN.value:
                return with_bearer_token(
                    backend_request,
                    creds[CredentialsVars.DHCORE_ACCESS_TOKEN.value],
                )
            case AuthType.BASIC.value:
                return with_basic_auth(
                    backend_request,
                    creds[CredentialsVars.DHCORE_USER.value],
                    creds[CredentialsVars.DHCORE_PASSWORD.value],
                )
        return replace(backend_request)

    @property
    def auth_type(self) -> str:
        return self._eval_auth_type()

    @property
    def credentials(self) -> dict:
        return self._credential_session.credentials

    @property
    def source(self) -> CredentialSource:
        return self._credential_session.source
