# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.credentials.configurator import Configurator
from digitalhub.stores.credentials.enums import CredsEnvVar


class SqlStoreConfigurator(Configurator):
    """
    Configure the store by getting the credentials from user
    provided config or from environment.
    """

    keys = [
        CredsEnvVar.DB_USERNAME.value,
        CredsEnvVar.DB_PASSWORD.value,
        CredsEnvVar.DB_HOST.value,
        CredsEnvVar.DB_PORT.value,
        CredsEnvVar.DB_DATABASE.value,
        CredsEnvVar.DB_PLATFORM.value,
    ]
    required_keys = [
        CredsEnvVar.DB_USERNAME.value,
        CredsEnvVar.DB_PASSWORD.value,
        CredsEnvVar.DB_HOST.value,
        CredsEnvVar.DB_PORT.value,
        CredsEnvVar.DB_DATABASE.value,
    ]

    def __init__(self):
        super().__init__()
        self.load_configs()

    ##############################
    # Configuration methods
    ##############################

    def load_env_vars(self) -> None:
        """
        Load the credentials from the environment.
        """
        env_creds = self._creds_handler.load_from_env(self.keys)
        self._creds_handler.set_credentials(self._env, env_creds)

    def load_file_vars(self) -> None:
        """
        Load the credentials from the file.
        """
        file_creds = self._creds_handler.load_from_file(self.keys)
        self._creds_handler.set_credentials(self._file, file_creds)

    def get_sql_conn_string(self) -> str:
        """
        Get the connection string from environment variables.

        Returns
        -------
        str
            The connection string.
        """
        creds = self.get_credentials(self._origin)
        user = creds[CredsEnvVar.DB_USERNAME.value]
        password = creds[CredsEnvVar.DB_PASSWORD.value]
        host = creds[CredsEnvVar.DB_HOST.value]
        port = creds[CredsEnvVar.DB_PORT.value]
        database = creds[CredsEnvVar.DB_DATABASE.value]
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
