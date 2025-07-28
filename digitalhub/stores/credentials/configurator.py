# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod

from digitalhub.stores.credentials.enums import CredsOrigin
from digitalhub.stores.credentials.handler import creds_handler
from digitalhub.utils.exceptions import ConfigError


class Configurator:
    # Must be set in implementing class
    keys: list[str] = []
    required_keys: list[str] = []

    # Origin of the credentials
    _env = CredsOrigin.ENV.value
    _file = CredsOrigin.FILE.value

    # Credentials handler
    _creds_handler = creds_handler

    def __init__(self):
        self._current_profile = self._creds_handler.get_current_profile()
        self.load_configs()
        self._changed_origin = False
        self._origin = self.set_origin()

    ##############################
    # Configuration
    ##############################

    def load_configs(self) -> None:
        """
        Load the configuration from the environment and from the file.
        """
        self.load_env_vars()
        self.load_file_vars()

    @abstractmethod
    def load_env_vars(self) -> None:
        ...

    @abstractmethod
    def load_file_vars(self) -> None:
        ...

    def check_config(self) -> None:
        """
        Check if the config is valid.

        Parameters
        ----------
        config : dict
            Configuration dictionary.

        Returns
        -------
        None
        """
        if (current := self._creds_handler.get_current_profile()) != self._current_profile:
            self.load_file_vars()
            self._current_profile = current

    def set_origin(self) -> str:
        """
        Evaluate the default origin from the credentials.

        Returns
        -------
        str
            The origin.
        """
        origin = self._env

        env_creds = self._creds_handler.get_credentials(self._env)
        missing_env = self._check_credentials(env_creds)

        file_creds = self._creds_handler.get_credentials(self._file)
        missing_file = self._check_credentials(file_creds)

        msg = ""
        if missing_env:
            msg = f"Missing required vars in env: {', '.join(missing_env)}"
            origin = self._file
            self._changed_origin = True
        elif missing_file:
            msg += f"Missing required vars in .dhcore.ini file: {', '.join(missing_file)}"

        if missing_env and missing_file:
            raise ConfigError(msg)

        return origin

    def eval_change_origin(self) -> None:
        """
        Try to change the origin of the credentials.
        If the origin has already been evaluated, raise an error.

        Returns
        -------
        None
        """
        try:
            self.change_origin()
        except ConfigError:
            raise ConfigError("Credentials origin already evaluated. Please check your credentials.")

    def change_origin(self) -> None:
        """
        Change the origin of the credentials.
        """
        if self._changed_origin:
            raise ConfigError("Origin has already been changed.")
        if self._origin == self._env:
            self.change_to_file()
        self.change_to_env()

    def change_to_file(self) -> None:
        """
        Change the origin to file.
        """
        if self._origin == self._env:
            self._changed_origin = True
        self._origin = CredsOrigin.FILE.value

    def change_to_env(self) -> None:
        """
        Change the origin to env.
        """
        if self._origin == self._file:
            self._changed_origin = True
        self._origin = CredsOrigin.ENV.value

    ##############################
    # Credentials
    ##############################

    def get_credentials(self, origin: str) -> dict:
        return self._creds_handler.get_credentials(origin)

    def _check_credentials(self, creds: dict) -> list[str]:
        missing_keys = []
        for k, v in creds.items():
            if v is None and k in self.required_keys:
                missing_keys.append(k)
        return missing_keys
