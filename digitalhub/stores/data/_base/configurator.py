# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.configurator.configurator import configurator
from digitalhub.stores.configurator.enums import CredsOrigin
from digitalhub.utils.exceptions import StoreError


class StoreConfigurator:
    # Must be set in implementing class
    keys: list[str] = []

    def __init__(self):
        self._get_env_config()
        self._get_file_config()

        # Check if there are any keys
        if not self.keys:
            raise StoreError("No list of keys to search for credentials.")

    def _get_env_config(self) -> None:
        """
        Get the store configuration from environment variables.

        Returns
        -------
        None
        """
        credentials = {var.value: configurator.load_from_env(var.value) for var in self.keys}
        configurator.set_credentials(CredsOrigin.ENV.value, credentials)

    def _get_file_config(self) -> None:
        """
        Get the store configuration from file.

        Returns
        -------
        None
        """
        credentials = {var.value: configurator.load_from_file(var.value) for var in self.keys}
        configurator.set_credentials(CredsOrigin.FILE.value, credentials)

    def refresh(self) -> None:
        self._get_env_config()
        self._get_file_config()
