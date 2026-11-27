# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from digitalhub.stores.client.common.enums import ConfigurationVars


def _get_config_file_path() -> Path:
    """
    Get the path to the configuration file.

    Returns
    -------
    Path
        Path to the configuration file.
    """
    dh_config_env = os.getenv(ConfigurationVars.DH_CONFIG.value)
    if dh_config_env is not None:
        try:
            return Path(dh_config_env)
        except (TypeError, ValueError):
            logging.getLogger(__name__).warning(
                "Invalid DH_CONFIG value %r; falling back to default config path",
                dh_config_env,
            )
            return Path.home() / ".dhcore.ini"
    return Path.home() / ".dhcore.ini"


@dataclass
class ClientConfig:
    """
    Tunable configuration for DHCore client behavior.

    Each client and credential provider receives its configuration
    explicitly; ``set_client_config()`` only changes the configuration of
    the default client built by ``get_client()``. Protocol constants shared
    with the backend live in ``digitalhub.stores.client.common.constants``.

    Attributes
    ----------
    http_timeout : int
        Default timeout for HTTP requests in seconds. Default: 60
    default_page_start : int
        Starting page number for pagination. Default: 0
    default_page_size : int
        Default number of items per page. Default: 25
    default_sort : str
        Default sorting for list operations. Default: "created,DESC"
    config_ini_path : Path
        Credentials file. Default: ``DH_CONFIG`` or ``~/.dhcore.ini``
    config_env_path : str
        Dotenv file next to the credentials file. Derived, not settable.
    max_refresh_attempts : int
        Maximum credential refresh attempts after an authentication failure. Default: 2
    """

    # HTTP request defaults
    http_timeout: int = 60

    # Pagination defaults
    default_page_start: int = 0
    default_page_size: int = 25
    default_sort: str = "created,DESC"

    # Configuration file path
    config_ini_path: Path = field(default_factory=_get_config_file_path)
    config_env_path: str = field(init=False)

    # Authentication defaults
    max_refresh_attempts: int = 2

    def __post_init__(self) -> None:
        if self.max_refresh_attempts < 1:
            raise ValueError("max_refresh_attempts must be at least 1")
        self.config_env_path = str(self.config_ini_path.parent / ".env")


def get_client_config() -> ClientConfig:
    """
    Get the client configuration of the session.

    The session builds it on first use, so ``DH_CONFIG`` is read then, like
    the other configuration variables, and not when ``digitalhub`` is imported.

    Returns
    -------
    ClientConfig
        Configuration of the session.
    """
    # Imported here: the session module imports this one.
    from digitalhub.stores.session import get_session

    return get_session().config


def set_client_config(config: ClientConfig) -> None:
    """
    Set the client configuration of the session.

    The session builds its next client with it; clients already built keep
    their own configuration.

    Parameters
    ----------
    config : ClientConfig
        New configuration to use globally.

    Examples
    --------
    >>> custom_config = ClientConfig(http_timeout=120, default_page_size=50)
    >>> set_client_config(custom_config)
    """
    from digitalhub.stores.session import get_session

    get_session().configure(config)


def reset_client_config() -> None:
    """
    Reset client configuration to default values.

    Examples
    --------
    >>> reset_client_config()
    """
    set_client_config(ClientConfig())
