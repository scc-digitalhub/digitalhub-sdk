# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.utils import build_log_path_from_source
from digitalhub.entities._constructors.uuid import build_uuid


def build_log_kwargs(
    project: str,
    name: str,
    entity_type: str,
    source: str | list[str],
    path: str | None = None,
    **kwargs,
) -> dict:
    """
    Build and enhance specification parameters for entity creation.

    Parameters
    ----------
    project : str
        The name of the project containing the entity.
    name : str
        The name of the entity.
    entity_type : str
        The type of the entity being created.
    source : str or list[str]
        The source specification(s) for the entity content.
        Can be a single source or multiple sources.
    path : str
        The destination path for the entity.
        If None, a path will be automatically generated.
    **kwargs : dict
        Additional specification parameters to be processed
        and passed to the entity creation.

    Returns
    -------
    dict
        The updated kwargs dictionary with processed path
        and UUID information included.
    """
    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        kwargs["path"] = build_log_path_from_source(project, entity_type, name, uuid, source)
    else:
        kwargs["path"] = path
    return kwargs
