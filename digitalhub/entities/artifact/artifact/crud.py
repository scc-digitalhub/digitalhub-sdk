# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.material.utils import kind_warning
from digitalhub.entities.artifact._base.crud import log_base_artifact, register_base_artifact
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact


def register_artifact(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    extensions: list[dict] | None = None,
    src_path: str | None = None,
    **kwargs,
) -> ArtifactArtifact:
    """
    Register an artifact entity for an existing source.

    Parameters
    ----------
    project : str
        Project name.
    source : SourcesOrListOfSources
        Path or URI of the existing artifact.
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
    src_path : str, optional
        Original source path stored in the artifact specification.
    **kwargs : dict
        Additional artifact specification parameters.

    Returns
    -------
    ArtifactArtifact
        Registered artifact entity.
    """
    return register_base_artifact(
        project=project,
        source=source,
        entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        src_path=src_path,
        **kwargs,
    )


def log_artifact(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    src_path: str | None = None,
    **kwargs,
) -> ArtifactArtifact:
    """
    Create an artifact entity and upload a local source.

    Parameters
    ----------
    project : str
        Project name.
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
    src_path : str, optional
        Original source path stored in the artifact specification.
    **kwargs : dict
        Additional artifact specification parameters.

    Returns
    -------
    ArtifactArtifact
        Created artifact entity with uploaded files.
    """
    kind_warning(
        requested_kind=kwargs.pop("kind", None),
        set_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        entity_type=EntityTypes.ARTIFACT.value,
    )
    return log_base_artifact(
        project=project,
        name=name,
        kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        version=version,
        description=description,
        labels=labels,
        src_path=src_path,
        **kwargs,
    )
