# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os

from digitalhub.stores.credentials.enums import SetCreds
from digitalhub.stores.credentials.ini_module import (
    load_file,
    load_key,
    load_profile,
    set_current_profile,
    write_config,
)
from digitalhub.stores.credentials.store import CredentialsStore


class CredentialHandler:
    """
    Configurator object used to configure clients and store credentials.
    """

    def __init__(self) -> None:
        self._creds_store = CredentialsStore()
        self._profile = self._read_current_profile()

    ##############################
    # Public methods
    ##############################

    def _read_current_profile(self) -> str:
        """
        Read the current credentials set.

        Returns
        -------
        str
            Credentials set name.
        """
        profile = os.getenv(SetCreds.DH_PROFILE.value)
        if profile is not None:
            return profile
        file = load_file()
        profile = load_profile(file)
        if profile is not None:
            return profile
        return SetCreds.DEFAULT.value

    def set_current_profile(self, creds_set: str) -> None:
        """
        Set the current credentials set.

        Parameters
        ----------
        creds_set : str
            Credentials set name.

        Returns
        -------
        None
        """
        self._profile = creds_set
        set_current_profile(creds_set)

    def get_current_profile(self) -> str:
        """
        Get the current credentials set.

        Returns
        -------
        str
            Credentials set name.
        """
        return self._profile

    def load_from_env(self, vars: list[str]) -> dict:
        """
        Load variable from env.

        Parameters
        ----------
        vars : str
            List of environment variable names.

        Returns
        -------
        dict
            Environment variable values.
        """
        return {var: os.getenv(var) for var in vars}

    def load_from_file(self, vars: list[str]) -> dict:
        """
        Load variables from config file.

        Parameters
        ----------
        vars : str
            List of environment variable names.

        Returns
        -------
        dict
            Environment variable values.
        """
        file = load_file()
        profile = load_profile(file)
        if profile is not None:
            self._profile = profile
        return {var: load_key(file, self._profile, var) for var in vars}

    def write_env(self, creds: dict) -> None:
        """
        Write the env variables to the .dhcore file.

        Parameters
        ----------
        creds : dict
            Credentials.

        Returns
        -------
        None
        """
        write_config(creds, self._profile)

    ##############################
    # Credentials store methods
    ##############################

    def set_credentials(self, origin: str, creds: dict) -> None:
        """
        Set credentials.

        Parameters
        ----------
        origin : str
            The origin of the credentials.
        creds : dict
            The credentials.

        Returns
        -------
        None
        """
        self._creds_store.set_credentials(self._profile, origin, creds)

    def get_credentials(self, origin: str) -> dict:
        """
        Get credentials from origin.

        Parameters
        ----------
        origin : str
            The origin of the credentials.

        Returns
        -------
        dict
            The credentials.
        """
        return self._creds_store.get_credentials(self._profile, origin)


# Define global credential handler
creds_handler = CredentialHandler()
