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
    Create a new object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    uuid : str
        ID of the object.
    version : str
        Version stored in entity metadata.
    description : str
        Description of the object (human readable).
    labels : list[str]
        List of labels.
    embedded : bool
        Flag to determine if object spec must be embedded in project spec.
    path : str
        Object path on local file system or remote storage. It is also the destination path of upload() method.
    extensions : list[dict]
        List of extensions.
    **kwargs : dict
        Spec keyword arguments.

    Returns
    -------
    Artifact
        Object instance.

    Examples
    --------
    >>> obj = new_artifact(project="my-project",
    >>>                    name="my-artifact",
    >>>                    kind="artifact",
    >>>                    path="s3://my-bucket/my-key")
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
) -> Artifact:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    source : SourcesOrListOfSources
        Artifact location on local path.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the artifact. If not provided, it's generated.
    version : str
        Version stored in entity metadata.
    description : str
        Artifact description.
    labels : list[str]
        Artifact labels.
    **kwargs : dict
        New artifact spec parameters.

    Returns
    -------
    Artifact
        Object instance.

    Examples
    --------
    >>> obj = log_base_artifact(project="my-project",
    >>>                         name="my-artifact",
    >>>                         kind="artifact",
    >>>                         source="./local-path")
    """
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
    """Register an artifact by creating an entity for an existing source."""
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
