# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.dataitem._base.crud import log_base_dataitem, register_base_dataitem
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.generic.entity import DataitemGeneric


def log_generic_dataitem(
    project: str,
    kind: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> DataitemGeneric:
    """
    Create and upload a dataitem of a dynamic kind.

    Parameters
    ----------
    project : str
        Project name.
    kind : str
        Entity kind.
    source : SourcesOrListOfSources
        Local dataitem source path or paths.
    name : str, optional
        Entity name. If omitted, it is inferred from ``source``.
    drop_existing : bool, default=False
        Whether to remove an existing entity with the same name.
    path : str, optional
        Destination path. If omitted, it is generated.
    version : str, optional
        Entity version.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    DataitemGeneric
        Created dataitem entity with uploaded files.
    """
    return log_base_dataitem(
        project=project,
        name=name,
        kind=kind,
        source=source,
        drop_existing=drop_existing,
        path=path,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )


def register_generic_dataitem(
    project: str,
    kind: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    extensions: list[dict] | None = None,
    **kwargs,
) -> DataitemGeneric:
    """
    Register a dataitem of a dynamic kind for an existing source.

    Parameters
    ----------
    project : str
        Project name.
    kind : str
        Entity kind.
    source : SourcesOrListOfSources
        Path or URI of the existing dataitem.
    name : str, optional
        Entity name. If omitted, it is inferred from ``source``.
    uuid : str, optional
        Entity identifier.
    version : str, optional
        Entity version.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    embedded : bool, default=False
        Whether to embed the entity specification in the project specification.
    extensions : list[dict], optional
        Entity extensions.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    DataitemGeneric
        Registered dataitem entity.
    """
    return register_base_dataitem(
        project=project,
        source=source,
        entity_kind=kind,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        **kwargs,
    )
