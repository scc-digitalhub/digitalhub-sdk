from __future__ import annotations

from enum import Enum


class EnvVar(Enum):
    """
    Environment variables.
    """

    ENDPOINT = "DHCORE_ENDPOINT"
    ISSUER = "DHCORE_ISSUER"
    USER = "DHCORE_USER"
    PASSWORD = "DHCORE_PASSWORD"
    CLIENT_ID = "DHCORE_CLIENT_ID"
    ACCESS_TOKEN = "DHCORE_ACCESS_TOKEN"
    REFRESH_TOKEN = "DHCORE_REFRESH_TOKEN"


class AuthType(Enum):
    """
    Authentication types.
    """

    BASIC = "basic"
    OAUTH2 = "oauth2"
