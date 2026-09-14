# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.stores.client.auth.enums import CredentialSource


class CredentialSession:
    """Own the active credentials and source selection for one client session."""

    def __init__(self, credentials: dict[str, Any]) -> None:
        self._credentials = credentials
        self._source = CredentialSource.FILE

    def use_file(self, credentials: dict[str, Any]) -> None:
        """Activate credentials loaded from the current file profile."""
        self._credentials = credentials
        self._source = CredentialSource.FILE

    def use_environment(self, credentials: dict[str, Any]) -> None:
        """Activate credentials loaded from environment variables."""
        self._credentials = credentials
        self._source = CredentialSource.ENV

    def update(self, credentials: dict[str, Any]) -> None:
        """Update active credentials without changing their source."""
        self._credentials.update(credentials)

    def retry(self, file_credentials: dict[str, Any], env_credentials: dict[str, Any]) -> bool:
        """Select the next credential source after a failed authentication attempt."""
        if self._source is CredentialSource.ENV:
            return False

        if self._credentials != file_credentials:
            self.use_file(file_credentials)
        else:
            self.use_environment(env_credentials)
        return True

    @property
    def credentials(self) -> dict[str, Any]:
        return self._credentials

    @property
    def source(self) -> CredentialSource:
        return self._source
