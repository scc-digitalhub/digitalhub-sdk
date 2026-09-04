# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.utils import build_log_name_from_source
from digitalhub.entities._mixin.material.utils import build_register_name, kind_warning
from digitalhub.entities._processors.processors import crud_processor, material_processor
from digitalhub.entities.artifact._base.utils import build_log_kwargs
from digitalhub.utils.file_utils import eval_local_source

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact._base.entity import Artifact
    from digitalhub.utils.types import SourcesOrListOfSources


def new_artifact(
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
) -> Artifact:
    """
    Create a new artifact entity in the backend.

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
    Artifact
        Created artifact entity.
    """
    return crud_processor.create_context_entity(
        project=project,
        name=name,
        kind=kind,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        entity_type=EntityTypes.ARTIFACT.value,
        path=path,
        extensions=extensions,
        **kwargs,
    )


def log_base_artifact(
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
)-> Artifact:
    """
    Create an artifact entity and upload a local source.

    Parameters
    ----------
    project : str
        Project name.
    kind : str
        Entity kind.
    source : SourcesOrListOfSources
        Local artifact source path or paths.
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
        Additional artifact specification parameters.

    Returns
    -------
    Artifact
        Created artifact entity with uploaded files.
    """
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    eval_local_source(source)
    if name is None:
        name = build_log_name_from_source(source)
    kwargs = build_log_kwargs(
        project,
        name,
        entity_type=EntityTypes.ARTIFACT.value,
        source=source,
        path=path,
        **kwargs,
    )
    return material_processor.log_material_entity(
        source=source,
        project=project,
        name=name,
        kind=kind,
        drop_existing=drop_existing,
        entity_type=EntityTypes.ARTIFACT.value,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )


def register_base_artifact(
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
) -> Artifact:
    """
    Register an artifact entity for an existing source.

    Parameters
    ----------
    project : str
        Project name.
    source : SourcesOrListOfSources
        Path or URI of the existing artifact.
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
        Additional artifact specification parameters.

    Returns
    -------
    Artifact
        Registered artifact entity.
    """
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    kind_warning(
        requested_kind=kwargs.pop("kind", None),
        set_kind=entity_kind,
        entity_type=EntityTypes.ARTIFACT.value,
    )
    name = build_register_name(
        name=name,
        source=source,
        entity_type=EntityTypes.ARTIFACT.value,
        entity_kind=entity_kind,
    )
    if isinstance(source, list):
        source = source[0]
    return new_artifact(
        project=project,
        name=name,
        kind=entity_kind,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        path=source,
        extensions=extensions,
        **kwargs,
    )
