# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client.common.enums import ConfigurationVars
from digitalhub.stores.client.factory import get_client
from digitalhub.stores.session import get_session

if typing.TYPE_CHECKING:
    from digitalhub.stores.data._base.store import Store


def get_default_store_uri(project_config: dict | None = None) -> str:
    """
    Resolve the default store URI from project settings or client configuration.

    Parameters
    ----------
    project_config : dict, optional
        Project-specific configuration.

    Returns
    -------
    str
        The default store URI.
    """
    var = ConfigurationVars.DEFAULT_FILES_STORE.value

    store = (project_config or {}).get(var.lower().replace("dhcore_", ""))
    if store is not None:
        return store

    store = get_client().get_credentials_and_config().get(var)

    if store is None or store == "":
        raise ValueError(
            "No default store found. "
            "Please set a default store "
            f"in your environment (e.g. export {var}=) "
            " in the .dhcore.ini file "
            "or set it in project config."
        )
    return store


def get_store(uri: str, project: str | None = None) -> Store:
    """
    Returns the session's store for the given URI.

    Parameters
    ----------
    uri : str
        The URI to parse.
    project : str, optional
        Project the data belongs to. Pass it whenever it is known: stores
        will use the project's credentials.

    Returns
    -------
    Store
        The store instance corresponding to the URI.
    """
    return get_session().store(uri, project)
