# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.auth.config_loader import ConfigLoader
from digitalhub.stores.client.auth.enums import ConfigurationVars, CredentialsVars
from digitalhub.stores.client.common.utils import sanitize_endpoint
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.generic_utils import list_enum


class ConfigManager:
    """
    Manages credentials and configuration for DHCore client.

    Handles loading credentials from environment variables and configuration files,
    manages profiles, and provides access to configuration and credentials.
    Supports validation and sanitization of endpoints.
    """

    keys = [*list_enum(ConfigurationVars), *list_enum(CredentialsVars)]

    def __init__(self) -> None:
        self._config_loader = ConfigLoader()
        self._reload_from_env = False
        self._validate()

    ##############################
    # Configuration methods
    ##############################

    def get_endpoint(self) -> str:
        """
        Get the configured DHCore backend endpoint.

        Returns the sanitized and validated endpoint URL from current credential source.

        Returns
        -------
        str
            DHCore backend endpoint URL.

        Raises
        ------
        KeyError
            If endpoint not configured in current credential source.
        """
        config = self.get_configuration()
        endpoint = config[ConfigurationVars.DHCORE_ENDPOINT.value]
        return sanitize_endpoint(endpoint)

    def get_configuration(self) -> dict:
        """
        Get current configuration.

        Returns
        -------
        dict
            Current configuration dictionary.
        """
        return self._config_loader.get_configuration()

    ##############################
    # Credentials methods
    ##############################

    def get_credentials(self) -> dict:
        """
        Get current credentials.

        Returns
        -------
        dict
            Current credentials dictionary.
        """
        return self._config_loader.get_credentials()

    def reload_credentials(self) -> None:
        """
        Reload credentials from environment and file.
        """
        self._config_loader.reload_credentials()

    def eval_retry(self) -> bool:
        """
        Evaluate credentials reload based on retry logic.

        Returns
        -------
        bool
            True if a retry action was performed, otherwise False.
        """
        current_creds = self.get_credentials()
        reread_creds = self._config_loader.load_credentials()

        # Compare cached and file credentials.
        # If different, reload in cache.
        if current_creds != reread_creds:
            self.reload_credentials()
            return True

        # Check if we need to reload from env only
        if not self._reload_from_env:
            self._config_loader.reload_credentials_from_env()
            self._reload_from_env = True
            return True

        return False

    def write_credentials(self, credentials: dict) -> None:
        """
        Save credentials to configuration file.

        Parameters
        ----------
        credentials : dict
            Credentials to save.
        """
        self._config_loader.write_file(credentials)

    ##############################
    # Profile methods
    ##############################

    def set_current_profile(self, profile: str) -> None:
        """
        Set the current credentials profile.

        Parameters
        ----------
        profile : str
            Name of the credentials profile to set.
        """
        self._config_loader.set_current_profile(profile)

    def get_current_profile(self) -> str:
        """
        Get the name of the current credentials profile.

        Returns
        -------
        str
            Name of the current credentials profile.
        """
        return self._config_loader.get_current_profile()

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
        return {**self.get_configuration(), **self.get_credentials()}

    def _validate(self) -> None:
        """
        Validate if all required keys are present in the configuration.
        """
        required_keys = [ConfigurationVars.DHCORE_ENDPOINT.value]
        current_keys = self.get_credentials_and_config()
        for key in required_keys:
            if current_keys.get(key) is None:
                raise ClientError(f"Required configuration key '{key}' is missing.")
