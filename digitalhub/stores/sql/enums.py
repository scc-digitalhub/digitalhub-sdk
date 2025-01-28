from __future__ import annotations

from enum import Enum


class SqlStoreEnv(Enum):
    """
    SqlStore environment
    """

    HOST = "DB_HOST"
    PORT = "DB_PORT"
    USER = "DB_USER"
    PASSWORD = "DB_PASSWORD"
    DATABASE = "DB_DATABASE"
    PG_SCHEMA = "DB_SCHEMA"
