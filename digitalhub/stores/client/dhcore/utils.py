# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import typing

from digitalhub.stores.client.api import get_client
from digitalhub.stores.credentials.enums import CredsEnvVar

if typing.TYPE_CHECKING:
    from digitalhub.stores.client.dhcore.client import ClientDHCore


def set_dhcore_env(
    endpoint: str | None = None,
    user: str | None = None,
    password: str | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
    client_id: str | None = None,
) -> None:
    """
    Function to set environment variables for DHCore config.
    Note that if the environment variable is already set, it
    will be overwritten.

    Parameters
    ----------
    endpoint : str
        The endpoint of DHCore.
    user : str
        The user of DHCore.
    password : str
        The password of DHCore.
    access_token : str
        The access token of DHCore.
    refresh_token : str
        The refresh token of DHCore.
    client_id : str
        The client id of DHCore.

    Returns
    -------
    None
    """
    if endpoint is not None:
        os.environ[CredsEnvVar.DHCORE_ENDPOINT.value] = endpoint
    if user is not None:
        os.environ[CredsEnvVar.DHCORE_USER.value] = user
    if password is not None:
        os.environ[CredsEnvVar.DHCORE_PASSWORD.value] = password
    if access_token is not None:
        os.environ[CredsEnvVar.DHCORE_ACCESS_TOKEN.value] = access_token
    if refresh_token is not None:
        os.environ[CredsEnvVar.DHCORE_REFRESH_TOKEN.value] = refresh_token
    if client_id is not None:
        os.environ[CredsEnvVar.DHCORE_CLIENT_ID.value] = client_id

    client: ClientDHCore = get_client(local=False)
    client._configurator.load_env_vars()


def refresh_token() -> None:
    """
    Function to refresh token.

    Returns
    -------
    None
    """
    client: ClientDHCore = get_client(local=False)
    client._configurator.check_config()
    client._configurator.get_new_access_token()
