# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.crud_factory import MaterialEntityCRUD

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.utils.types import SourcesOrListOfSources


_crud: MaterialEntityCRUD[Dataitem] = MaterialEntityCRUD(EntityTypes.DATAITEM.value)


def new_dataitem(
    project: str,
    name: str,
    kind: str,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    path: str | None = None,
    extensions: list[dict] | None = None,
    **kwargs,
) -> Dataitem:
    """
    Create a new dataitem entity in the backend.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Entity name.
    kind : str
        Entity kind.
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
    path : str, optional
        Entity path on the local file system or remote storage. It is also the
        destination path for uploads.
    extensions : list[dict], optional
        Entity extensions.
    **kwargs : dict
        Additional entity specification parameters.

    Returns
    -------
    Dataitem
        Created dataitem entity.
    """
    return _crud.create(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        path=path,
        extensions=extensions,
        **kwargs,
    )


def log_base_dataitem(
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
) -> Dataitem:
    """
    Create a dataitem entity and upload a local source.

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
        Additional dataitem specification parameters.

    Returns
    -------
    Dataitem
        Created dataitem entity with uploaded files.
    """
    return _crud.log(
        project=project,
        kind=kind,
        source=source,
        name=name,
        drop_existing=drop_existing,
        path=path,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )


def register_base_dataitem(
    project: str,
    source: SourcesOrListOfSources,
    entity_kind: str,
    name: str | None = None,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    extensions: list[dict] | None = None,
    **kwargs,
) -> Dataitem:
    """
    Register a dataitem entity for an existing source.

    Parameters
    ----------
    project : str
        Project name.
    source : SourcesOrListOfSources
        Path or URI of the existing dataitem.
    entity_kind : str
        Entity kind.
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
    Dataitem
        Registered dataitem entity.
    """
    return _crud.register(
        new_dataitem,
        project=project,
        source=source,
        entity_kind=entity_kind,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        **kwargs,
    )
