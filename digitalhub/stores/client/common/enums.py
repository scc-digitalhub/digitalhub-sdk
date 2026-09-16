# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum


class AuthType(Enum):
    """
    Authentication types.
    """

    BASIC = "basic"
    OAUTH2 = "oauth2"
    EXCHANGE = "exchange"
    ACCESS_TOKEN = "access_token_only"
    NO_AUTH = "no_auth"


class SetCreds(Enum):
    """
    Supported credential environments.
    """

    DEFAULT = "__default"
    DH_PROFILE = "DH_NAME"


class CredentialSource(Enum):
    """Active source of credentials for the current client session."""

    FILE = "file"
    ENV = "env"


class ConfigurationVars(Enum):
    """
    List of supported configuration variables.
    """

    # Configuration
    DH_CONFIG = "DH_CONFIG"

    # S3
    S3_ENDPOINT_URL = "AWS_ENDPOINT_URL"
    S3_REGION = "AWS_REGION"
    S3_SIGNATURE_VERSION = "S3_SIGNATURE_VERSION"
    S3_PATH_STYLE = "S3_PATH_STYLE"
    S3_BUCKET = "S3_BUCKET"

    # SQL
    DB_HOST = "DB_HOST"
    DB_PORT = "DB_PORT"
    DB_DATABASE = "DB_DATABASE"
    DB_PLATFORM = "DB_PLATFORM"
    DB_PG_SCHEMA = "DB_SCHEMA"

    # DHCORE
    DHCORE_ENDPOINT = "DHCORE_ENDPOINT"
    DHCORE_ISSUER = "DHCORE_ISSUER"
    DHCORE_WORKFLOW_IMAGE = "DHCORE_WORKFLOW_IMAGE"
    DHCORE_CLIENT_ID = "DHCORE_CLIENT_ID"
    DEFAULT_FILES_STORE = "DHCORE_DEFAULT_FILES_STORE"
    DH_PROJECTS = "DH_PROJECTS"
    DHCORE_NAME = "DHCORE_NAME"
    DHCORE_NAMESPACE = "DHCORE_NAMESPACE"
    DHCORE_PROXY = "DHCORE_PROXY"
    DHCORE_VERSION = "DHCORE_VERSION"

    # OAUTH2
    OAUTH2_TOKEN_ENDPOINT = "OAUTH2_TOKEN_ENDPOINT"


class CredentialsVars(Enum):
    """
    List of supported credential variables.
    """

    # S3
    S3_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
    S3_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
    S3_SESSION_TOKEN = "AWS_SESSION_TOKEN"
    S3_CREDENTIALS_EXPIRATION = "AWS_CREDENTIALS_EXPIRATION"

    # SQL
    DB_USERNAME = "DB_USERNAME"
    DB_PASSWORD = "DB_PASSWORD"

    # DHCORE
    DHCORE_USER = "DHCORE_USER"
    DHCORE_PASSWORD = "DHCORE_PASSWORD"
    DHCORE_ACCESS_TOKEN = "DHCORE_ACCESS_TOKEN"
    DHCORE_REFRESH_TOKEN = "DHCORE_REFRESH_TOKEN"
    DHCORE_PERSONAL_ACCESS_TOKEN = "DHCORE_PERSONAL_ACCESS_TOKEN"
    DHCORE_EXPIRES_IN = "DHCORE_EXPIRES_IN"
    DHCORE_ID_TOKEN = "DHCORE_ID_TOKEN"


class ApiType(Enum):
    """
    API categories.
    """

    BASE = "base"
    CONTEXT = "context"


class HttpMethod(str, Enum):
    """HTTP methods used by compiled backend requests."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class OpsType(Enum):
    """Observable operation types for backend requests."""

    HTTP_REQUEST = "http.request"
    ENTITY_CREATE = "entity.create"
    ENTITY_READ = "entity.read"
    ENTITY_UPDATE = "entity.update"
    ENTITY_DELETE = "entity.delete"
    ENTITY_LIST = "entity.list"
    ENTITY_SEARCH = "entity.search"
    AUTH_REFRESH = "auth.refresh"
    AUTH_DISCOVERY = "auth.discovery"
    AUTH_VALIDATE = "auth.validate"
    CONFIG_K8S_RESOURCE_PROFILES = "config.k8s_resource_profiles"


class BackendOp(Enum):
    """
    Backend operations.
    """

    CREATE = "create"
    READ = "read"
    READ_ALL_VERSIONS = "read_all_versions"
    UPDATE = "update"
    DELETE = "delete"
    DELETE_ALL_VERSIONS = "delete_all_versions"
    LIST = "list"
    LIST_FIRST = "list_first"
    STOP = "stop"
    RESUME = "resume"
    DATA = "data"
    FILES = "files"
    LOGS = "logs"
    SEARCH = "search"
    SHARE = "share"
    METRICS = "metrics"
    SHARE_READ = "share_read"
    UNSHARE = "unshare"
    DATA_READ = "data_read"
    DATA_UPDATE = "data_update"
    FILES_READ = "files_read"
    FILES_UPDATE = "files_update"
    LOGS_READ = "logs_read"
    METRICS_READ = "metrics_read"
    METRICS_UPDATE = "metrics_update"
