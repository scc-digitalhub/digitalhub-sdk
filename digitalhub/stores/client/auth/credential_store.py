# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import Any

from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.client.auth.file_module import (
    load_dotenv_file,
    load_file,
    load_key,
    write_dotenv,
    write_file,
)
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.generic_utils import list_enum
from digitalhub.utils.logger.logger import get_logger

logger = get_logger(__name__)


class CredentialStore:
    """Load configuration and credentials from the supported local sources."""

    def __init__(self, profile: str) -> None:
        self._profile = profile

    def load_configuration(self) -> dict[str, Any]:
        """Load configuration with file values taking precedence over env values."""
        return self._load(ConfigurationVars)

    def load_credentials(self) -> dict[str, Any]:
        """Load credentials with file values taking precedence over env values."""
        return self._load(CredentialsVars)

    def load_credentials_from_env(self) -> dict[str, Any]:
        """Load credentials from environment variables only."""
        return self._read_env(list_enum(CredentialsVars))

    def export_to_ini(self, variables: dict) -> None:
        """Write credentials/configuration to the active profile."""
        try:
            write_file(variables, self._profile)
        except (ClientError, OSError):
            raise ClientError("Failed to write credentials to file.")

    def export_to_env(self, variables: dict) -> None:
        """Write credentials/configuration to the dotenv file."""
        try:
            write_dotenv(variables)
        except (ClientError, OSError):
            logger.debug("Failed to write credentials to .env file.")

    def load_to_env(self) -> None:
        """Load credentials/configuration from the dotenv file into the environment."""
        try:
            load_dotenv_file()
        except (ClientError, OSError):
            logger.debug("Failed to load credentials from .env file.")

    def _load(self, variables: type[ConfigurationVars] | type[CredentialsVars]) -> dict[str, Any]:
        keys = list_enum(variables)
        env_values = self._read_env(keys)
        file_values = self._read_file(keys, self._profile)
        return {**env_values, **{key: value for key, value in file_values.items() if value is not None}}

    @staticmethod
    def _read_env(variables: list[str]) -> dict[str, Any]:
        return {variable: os.getenv(variable) for variable in variables}

    @staticmethod
    def _read_file(variables: list[str], profile: str) -> dict[str, Any]:
        file = load_file()
        return {variable: load_key(file, profile, variable) for variable in variables}
