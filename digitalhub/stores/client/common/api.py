# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.base.factory import get_client


def refresh_token() -> None:
    """
    Refresh the current OAuth2 access token.

    Uses the refresh token stored in client configuration to obtain a new
    access token. Requires OAuth2 authentication configuration.


    Raises
    ------
    ClientError
        If client not properly configured or token refresh fails.
    """
    get_client().refresh_token()


def get_credentials_and_config() -> dict:
    """
    Get current client credentials and configuration.

    Returns
    -------
    dict
        Current client credentials and configuration details.
    """
    return get_client().get_credentials_and_config()


def set_current_profile(profile: str) -> None:
    """
    Set the current credentials profile.

    Parameters
    ----------
    profile : str
        Name of the credentials profile to set.
    """
    get_client().set_current_profile(profile)


def get_current_profile() -> str:
    """
    Get the name of the current credentials profile.

    Returns
    -------
    str
        Name of the current credentials profile.
    """
    return get_client().get_current_profile()
