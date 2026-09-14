# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import Any, ClassVar

from digitalhub.stores.client.auth.credential_store import CredentialStore
from digitalhub.stores.client.auth.credential_session import CredentialSession
from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialSource, CredentialsVars, SetCreds
from digitalhub.stores.client.auth.file_module import (
    load_file,
    load_profile,
    set_current_profile,
)
from digitalhub.stores.client.common.utils import sanitize_endpoint
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.generic_utils import list_enum
from digitalhub.utils.logger.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages credentials and configuration for DHCore client."""

    keys: ClassVar[list[str]] = [*list_enum(ConfigurationVars), *list_enum(CredentialsVars)]

    def __init__(self) -> None:
        self._current_profile = self._read_current_profile()
        self._credential_store = CredentialStore(self._current_profile)
        self._configuration: dict[str, Any] = self.load_configuration()
        self._credential_session = CredentialSession(self.load_credentials())
        self._validate()
        self._in_memory: bool = False

    @staticmethod
    def _read_current_profile() -> str:
        """Read the current credentials profile name."""
        profile = os.getenv(SetCreds.DH_PROFILE.value)
        if profile is not None:
            return profile

        try:
            file = load_file()
            return load_profile(file)
        except ClientError:
            pass

        return SetCreds.DEFAULT.value

    def set_current_profile(self, profile: str) -> None:
        """Set the current credentials profile name."""
        if self._in_memory:
            raise ClientError("Cannot set profile when configuration is in-memory only.")

        set_current_profile(profile)
        self._current_profile = profile
        self._credential_store = CredentialStore(profile)
        self.reload_configuration()
        self.reload_credentials()

    def load_configuration(self) -> dict[str, Any]:
        """Load configuration with file > env precedence."""
        return self._credential_store.load_configuration()

    def reload_configuration(self) -> None:
        """Reload configuration from environment and file."""
        self._configuration = self.load_configuration()

    def get_endpoint(self) -> str:
        """Get the configured DHCore backend endpoint."""
        endpoint = self._configuration[ConfigurationVars.DHCORE_ENDPOINT.value]
        return sanitize_endpoint(endpoint)

    def load_credentials(self) -> dict[str, Any]:
        """Load credentials with file > env precedence."""
        return self._credential_store.load_credentials()

    def reload_credentials(self) -> None:
        """Reload credentials from environment and file."""
        self._credential_session.use_file(self.load_credentials())

    def eval_retry(self) -> bool:
        """Evaluate credentials reload based on retry logic."""
        if self.credential_source is CredentialSource.ENV:
            logger.debug("Credential source is already environment variables; stopping the refresh cycle.")
            return False

        should_retry = self._credential_session.retry(
            self.load_credentials(),
            self._credential_store.load_credentials_from_env(),
        )
        if self.credential_source is CredentialSource.FILE:
            logger.debug("File credentials changed; reloading credentials from the active profile.")
        else:
            logger.debug("File credential retry did not resolve authentication; switching to environment variables.")
        return should_retry

    def export_to_ini(self, variables: dict) -> None:
        """Write credentials/configuration to the .dhcore file."""
        self._credential_store.export_to_ini(variables)

    def export_to_env(self, variables: dict) -> None:
        """Write credentials/configuration to the .env file."""
        self._credential_store.export_to_env(variables)

    def load_to_env(self) -> None:
        """Load credentials/configuration to environment variables."""
        self._credential_store.load_to_env()

    def save_credentials(self, variables: dict) -> None:
        """Save refreshed credentials to the active storage."""
        if self._in_memory:
            logger.debug("Persisting refreshed credentials in memory only.")
            self._credential_session.update({key.upper(): value for key, value in variables.items()})
            return

        try:
            self.export_to_ini(variables)
        except (ClientError, OSError):
            self._in_memory = True
            self._credential_session.update({key.upper(): value for key, value in variables.items()})
            logger.warning("Credential persistence failed; refreshed credentials will remain in memory only.")
            return

        self.export_to_env(variables)
        if self.credential_source is CredentialSource.ENV:
            self._credential_session.update({key.upper(): value for key, value in variables.items()})
            logger.debug("Persisted refreshed credentials and kept environment credentials active in memory.")
        else:
            self.reload_credentials()
            logger.debug("Persisted refreshed credentials and reloaded the active file profile.")
        self.load_to_env()

    def get_credentials_and_config(self) -> dict:
        """Get current authentication credentials and configuration."""
        return {**self._configuration, **self.credentials}

    def _validate(self) -> None:
        """Validate if all required keys are present in the configuration."""
        required_keys = [ConfigurationVars.DHCORE_ENDPOINT.value]
        current_keys = {**self._configuration, **self.credentials}
        for key in required_keys:
            if current_keys.get(key) is None:
                raise ClientError(f"Required configuration key '{key}' is missing.")

    @property
    def in_memory(self) -> bool:
        return self._in_memory

    @property
    def current_profile(self) -> str:
        return self._current_profile

    @property
    def credential_source(self) -> CredentialSource:
        return self._credential_session.source

    @property
    def credential_session(self) -> CredentialSession:
        return self._credential_session

    @property
    def configuration(self) -> dict:
        return self._configuration

    @property
    def credentials(self) -> dict:
        return self._credential_session.credentials
