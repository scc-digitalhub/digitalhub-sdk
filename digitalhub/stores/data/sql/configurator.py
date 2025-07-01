# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.configurator.configurator import configurator
from digitalhub.stores.data._base.configurator import StoreConfigurator
from digitalhub.stores.data.sql.enums import SqlStoreEnv


class SqlStoreConfigurator(StoreConfigurator):
    """
    Configure the store by getting the credentials from user
    provided config or from environment.
    """

    keys = [
        SqlStoreEnv.USERNAME,
        SqlStoreEnv.PASSWORD,
        SqlStoreEnv.HOST,
        SqlStoreEnv.PORT,
        SqlStoreEnv.DATABASE,
    ]

    ##############################
    # Configuration methods
    ##############################

    @staticmethod
    def get_sql_conn_string(origin: str) -> str:
        """
        Get the connection string from environment variables.

        Parameters
        ----------
        origin : str
            The origin of the credentials.

        Returns
        -------
        str
            The connection string.
        """
        creds = configurator.get_credentials(origin)
        user = creds[SqlStoreEnv.USERNAME.value]
        password = creds[SqlStoreEnv.PASSWORD.value]
        host = creds[SqlStoreEnv.HOST.value]
        port = creds[SqlStoreEnv.PORT.value]
        database = creds[SqlStoreEnv.DATABASE.value]
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
