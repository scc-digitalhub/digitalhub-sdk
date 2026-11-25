# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from sqlalchemy.engine import URL

from digitalhub.stores.client.common.enums import ConfigurationVars, CredentialsVars

if typing.TYPE_CHECKING:
    from digitalhub.stores.data._base.credentials import StoreCredentials


class SqlStoreConfigurator:
    """
    Configurator class for SQL store configuration and credentials management.
    """

    def __init__(self, credentials: StoreCredentials) -> None:
        self._credentials = credentials
        self._validate()

    def get_sql_conn_string(self) -> str:
        """
        Generate PostgreSQL connection string from stored credentials.

        Returns
        -------
        str
            A PostgreSQL connection string in the format:
            'postgresql+pg8000://username:password@host:port/database'
        """
        creds = self.get_credentials(lowercase_keys=False)
        user = creds[CredentialsVars.DB_USERNAME.value]
        password = creds[CredentialsVars.DB_PASSWORD.value]
        host = creds[ConfigurationVars.DB_HOST.value]
        port = creds[ConfigurationVars.DB_PORT.value]
        database = creds[ConfigurationVars.DB_DATABASE.value]
        return URL.create(
            drivername="postgresql+pg8000",
            username=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
        ).render_as_string(hide_password=False)

    def get_credentials(self, lowercase_keys: bool = True) -> dict:
        """
        Get all configured database credentials as a dictionary.

        Parameters
        ----------
        lowercase_keys : bool
            Whether to return credential keys in lowercase format.

        Returns
        -------
        dict
            Dictionary containing all credential key-value pairs from self.keys.
            Keys correspond to database connection parameters such as
            username, password, host, port, database, and platform.
        """
        keys = [
            CredentialsVars.DB_USERNAME.value,
            CredentialsVars.DB_PASSWORD.value,
            ConfigurationVars.DB_HOST.value,
            ConfigurationVars.DB_PORT.value,
            ConfigurationVars.DB_DATABASE.value,
        ]
        creds = self._credentials.get()
        if lowercase_keys:
            return {key.lower(): creds.get(key) for key in keys}
        return {key: creds.get(key) for key in keys}

    def eval_retry(self) -> bool:
        """
        Evaluate the status of retry lifecycle.

        Returns
        -------
        bool
            True if a retry should be attempted, False otherwise.
        """
        return self._credentials.refresh()

    def _validate(self) -> None:
        """
        Validate if all required keys are present in the configuration.
        """
        required_keys = [
            ConfigurationVars.DB_HOST.value,
            ConfigurationVars.DB_PORT.value,
            ConfigurationVars.DB_DATABASE.value,
            CredentialsVars.DB_USERNAME.value,
            CredentialsVars.DB_PASSWORD.value,
        ]
        current_keys = self._credentials.get()
        missing_keys = []
        for key in required_keys:
            if key not in current_keys or current_keys[key] is None:
                missing_keys.append(key)
        if missing_keys:
            raise ValueError(f"Missing required variables for SQL store: {', '.join(missing_keys)}")
