# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClientConfig:
    """
    Configuration for DHCore client behavior.

    Centralizes all configurable values for HTTP requests, pagination,
    and API interactions. All values have sensible defaults but can be
    customized as needed.

    Attributes
    ----------
    http_timeout : int
        Default timeout for HTTP requests in seconds. Default: 60
    default_page_start : int
        Starting page number for pagination. Default: 0
    default_page_size : int
        Default number of items per page. Default: 25
    default_sort : str
        Default sorting for list operations. Default: "metadata.updated,DESC"
    """

    # HTTP request defaults
    http_timeout: int = 60

    # Pagination defaults
    default_page_start: int = 0
    default_page_size: int = 25
    default_sort: str = "metadata.updated,DESC"

    # API level defaults
    max_api_level: int = 20
    min_api_level: int = 14
    lib_version: int = 15

    # Configuration file path
    config_file_path: Path = Path.home() / ".dhcore.ini"

    # API structure
    api_base: str = "/api/v1"
    api_context: str = "/api/v1/-"

    ##################################
    # AUTHENTICATION
    ##################################

    # Authentication defaults
    oauth2_grant_type: str = "refresh_token"
    oauth2_scope: str = "credentials"

    # PAT exchange defaults
    pat_subject_token_type: str = "urn:ietf:params:oauth:token-type:pat"
    pat_grant_type: str = "urn:ietf:params:oauth:grant-type:token-exchange"
    pat_scope: str = "credentials"

    # Prefixes vars
    dhcore: str = "dhcore_"
    oauth2: str = "oauth2_"


# Global default configuration instance
_default_config = ClientConfig()


def get_client_config() -> ClientConfig:
    """
    Get the current global client configuration.

    Returns
    -------
    ClientConfig
        Current global configuration instance.
    """
    return _default_config


def set_client_config(config: ClientConfig) -> None:
    """
    Set the global client configuration.

    Parameters
    ----------
    config : ClientConfig
        New configuration to use globally.

    Examples
    --------
    >>> custom_config = ClientConfig(http_timeout=120, default_page_size=50)
    >>> set_client_config(custom_config)
    """
    global _default_config
    _default_config = config


def reset_client_config() -> None:
    """
    Reset client configuration to default values.

    Examples
    --------
    >>> reset_client_config()
    """
    global _default_config
    _default_config = ClientConfig()
