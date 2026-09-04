# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.material.utils import kind_warning
from digitalhub.entities.dataitem._base.crud import log_base_dataitem, register_base_dataitem
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.dataitem.entity import DataitemDataitem


def log_dataitem(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> DataitemDataitem:
    """
    Create and upload a dataitem entity.

    Parameters
    ----------
    project : str
        Project name.
    name : str, optional
        Entity name. If omitted, it is inferred from ``source``.
    source : SourcesOrListOfSources
        Local dataitem source path or paths.
    drop_existing : bool, default=False
        Whether to drop existing entity with the same name.
    path : str, optional
        Destination path. If omitted, it is generated.
    version : str, optional
        Entity version.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    **kwargs : dict
        Additional dataitem specification parameters.

    Returns
    -------
    DataitemDataitem
        Created dataitem entity with uploaded files.
    """
    kind_warning(
        requested_kind=kwargs.pop("kind", None),
        set_kind=EntityKinds.DATAITEM_DATAITEM.value,
        entity_type=EntityTypes.DATAITEM.value,
    )
    return log_base_dataitem(
        project=project,
        name=name,
        kind=EntityKinds.DATAITEM_DATAITEM.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )


def register_dataitem(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    extensions: list[dict] | None = None,
    **kwargs,
) -> DataitemDataitem:
    """
    Register a dataitem entity for an existing source.

    Parameters
    ----------
    project : str
        Project name.
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
        Additional dataitem specification parameters.

    Returns
    -------
    DataitemDataitem
        Registered dataitem entity.
    """
    return register_base_dataitem(
        project=project,
        source=source,
        entity_kind=EntityKinds.DATAITEM_DATAITEM.value,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        **kwargs,
    )
