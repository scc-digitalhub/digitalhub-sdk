# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import Any
from warnings import warn

from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars, SetCreds
from digitalhub.stores.client.auth.ini_module import (
    file_exists,
    load_file,
    load_key,
    load_profile,
    set_current_profile,
    write_file,
)
from digitalhub.stores.client.common.utils import sanitize_endpoint
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.generic_utils import list_enum


class ConfigManager:
    """
    Manages credentials and configuration for DHCore client.
    """

    # List of all configuration and credential keys for easy access and validation.
    keys = [*list_enum(ConfigurationVars), *list_enum(CredentialsVars)]

    def __init__(self) -> None:
        # Current credentials profile name.
        self._current_profile = self._read_current_profile()

        # Configurations (endpoint, client id, etc.) and credentials (tokens, username/password).
        self._configuration: dict[str, Any] = self.load_configuration()
        self._credentials: dict[str, Any] = self.load_credentials()
        self._validate()

        # Indicates if configuration is stored in-memory only (True) or persisted to file (False).
        self._in_memory: bool = False

        # Try to write initial configuration to file if it does not exist yet. If writing fails, switch to in-memory mode.
        self._write_file()

        # Flag to indicate if credentials have been reloaded from environment variables during retry logic.
        self._reloaded_from_env: bool = False

    ##############################
    # Profile methods
    ##############################

    @staticmethod
    def _read_current_profile() -> str:
        """
        Read the current credentials profile name.

        Returns
        -------
        str
            Name of the credentials profile.
        """
        # Try to read profile from environment variable first.
        profile = os.getenv(SetCreds.DH_PROFILE.value)
        if profile is not None:
            return profile

        # If not found in environment, try to read from file.
        try:
            file = load_file()
            return load_profile(file)
        except ClientError:
            pass

        # If not found in file, return default profile name.
        return SetCreds.DEFAULT.value

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile name.

        Parameters
        ----------
        profile : str
            Name of the credentials profile to set.
        """
        if self._in_memory:
            raise ClientError("Cannot set profile when configuration is in-memory only.")

        set_current_profile(profile)
        self._current_profile = profile
        self.reload_configuration()
        self.reload_credentials()

    ##############################
    # Configuration methods
    ##############################

    def load_configuration(self) -> dict[str, Any]:
        """
        Load configuration with env > file precedence.

        Returns
        -------
        dict
            Merged configuration dictionary.
        """
        variables = list_enum(ConfigurationVars)
        env_config = self._read_env(variables)
        file_config = self._read_file(variables, self._current_profile)
        return {**file_config, **{k: v for k, v in env_config.items() if v is not None}}

    def reload_configuration(self) -> None:
        """
        Reload configuration from environment and file.
        """
        self._configuration = self.load_configuration()

    def get_endpoint(self) -> str:
        """
        Get the configured DHCore backend endpoint.

        Returns the sanitized and validated endpoint URL from current credential source.

        Returns
        -------
        str
            DHCore backend endpoint URL.
        """
        endpoint = self._configuration[ConfigurationVars.DHCORE_ENDPOINT.value]
        return sanitize_endpoint(endpoint)

    ##############################
    # Credentials methods
    ##############################

    def load_credentials(self) -> dict[str, Any]:
        """
        Load credentials with file > env precedence.

        Parameters
        ----------
        profile : str
            Profile name to load credentials from.

        Returns
        -------
        dict
            Merged credentials dictionary.
        """
        variables = list_enum(CredentialsVars)
        env_config = self._read_env(variables)
        file_config = self._read_file(variables, self.current_profile)
        return {**env_config, **{k: v for k, v in file_config.items() if v is not None}}

    def reload_credentials(self) -> None:
        """
        Reload credentials from environment and file.
        """
        self._credentials = self.load_credentials()

    def reload_credentials_from_env(self) -> None:
        """
        Reload credentials from environment where env > file precedence.
        Its a partial reload only from env variables used as fallback.
        """
        variables = list_enum(CredentialsVars)
        env_config = self._read_env(variables)
        file_config = self._read_file(variables, self.current_profile)
        self._credentials = {**file_config, **{k: v for k, v in env_config.items() if v is not None}}

    def eval_retry(self) -> bool:
        """
        Evaluate credentials reload based on retry logic.

        Returns
        -------
        bool
            True if a retry action was performed, otherwise False.
        """
        # Compare cached and file credentials. If different, reload in cache.
        if self._credentials != self.load_credentials():
            self.reload_credentials()
            return True

        # Check if we need to reload from env only
        if not self._reloaded_from_env:
            self.reload_credentials_from_env()
            self._reloaded_from_env = True
            return True

        return False

    ##############################
    # Export methods
    ##############################

    def export_to_file(self, variables: dict) -> None:
        """
        Write credentials/configuration to the .dhcore file.

        Parameters
        ----------
        variables : dict
            Variables to save.
        """
        try:
            write_file(variables, self._current_profile)
        except Exception:
            raise ClientError("Failed to write credentials to file.")

    def update_in_memory(self, variables: dict) -> None:
        """
        Update credentials in memory and persist to file.

        Parameters
        ----------
        variables : dict
            Variables to update.
        """
        self._credentials.update(variables)

    def _write_file(self) -> None:
        """
        Write current configuration and credentials to the .dhcore file
        if file does not exist yet.
        """
        try:
            if not file_exists():
                variables = {k: v for k, v in {**self._configuration, **self._credentials}.items() if v is not None}
                self.export_to_file(variables)
        except Exception:
            self._in_memory = True
            warn("Configuration file is not writable. Credentials will be stored in memory only for this session.")

    ##############################
    # Utility methods
    ##############################

    def get_credentials_and_config(self) -> dict:
        """
        Get current authentication credentials and configuration.

        Returns
        -------
        dict
            Current authentication credentials and configuration.
        """
        return {**self._configuration, **self._credentials}

    ##############################
    # Private methods
    ##############################

    def _validate(self) -> None:
        """
        Validate if all required keys are present in the configuration.
        """
        required_keys = [ConfigurationVars.DHCORE_ENDPOINT.value]
        current_keys = {**self._configuration, **self._credentials}
        for key in required_keys:
            if current_keys.get(key) is None:
                raise ClientError(f"Required configuration key '{key}' is missing.")

    @staticmethod
    def _read_env(variables: list) -> dict:
        """
        Read configuration variables from the .dhcore file.

        Parameters
        ----------
        variables : list
            List of environment variable names to read.

        Returns
        -------
        dict
            Dictionary of environment variables.
        """
        return {var: os.getenv(var) for var in variables}

    @staticmethod
    def _read_file(variables: list, profile: str) -> dict:
        """
        Read configuration variables from the .dhcore file.

        Parameters
        ----------
        variables : list
            List of environment variable names to read.
        profile : str
            Profile name to read from.

        Returns
        -------
        dict
            Dictionary of configuration variables.
        """
        file = load_file()
        return {var: load_key(file, profile, var) for var in variables}

    ###############################
    # Properties
    ###############################

    @property
    def in_memory(self) -> bool:
        return self._in_memory

    @property
    def current_profile(self) -> str:
        return self._current_profile

    @property
    def configuration(self) -> dict:
        return self._configuration

    @property
    def credentials(self) -> dict:
        return self._credentials
