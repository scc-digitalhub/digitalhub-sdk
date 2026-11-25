# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

# Module import, resolved at call time: digitalhub.stores.session imports this
# package, so it may still be initializing when this module loads.
from digitalhub.stores import session as _session

if typing.TYPE_CHECKING:
    from digitalhub.stores.client.client import Client


def get_client() -> Client:
    """
    Get the user client of the session.

    Returns
    -------
    Client
        The client instance.

    Examples
    --------
    Get the client of the session:
    >>> client = get_client()

    """
    return _session.get_session().client()


def resolve_client(project: str | None = None) -> Client:
    """
    Resolve the client for a backend operation at the time of the operation.

    This is the single resolution point used by entities, contexts and
    processors. Callers must not keep the result: resolving on every use is
    what lets ``set_client_config()`` and future per-project credentials take
    effect everywhere.

    Parameters
    ----------
    project : str, optional
        Name of the project the operation targets. ``None`` for operations
        that are not scoped to a project's resources, such as listing or
        creating projects. Every project currently shares the default client;
        the parameter is the hook for per-project credentials.

    Returns
    -------
    Client
        The client to use for the operation.
    """
    return _session.get_session().client(project)
