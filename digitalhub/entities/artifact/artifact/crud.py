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
    **kwargs,
) -> ArtifactArtifact:
    """Register an artifact that already exists in a supported store.

    This is a shortcut for creating an artifact whose specification points
    to an existing path. Unlike :func:`log_artifact`, it does not upload any
    data and leaves the source path unchanged. Use it when a file is already
    available, for example, at an S3 or HTTP URI.

    Parameters
    ----------
    project : str
        Project name.
    source : SourcesOrListOfSources
        Path or URI of the existing artifact. The format must be supported by
        one of the configured stores, for example ``s3://bucket/key``.
    name : str, optional
        Artifact name. If omitted, it is inferred from the final component of
        ``source``.
    uuid : str, optional
        ID of the artifact.
    version : str, optional
        Version stored in artifact metadata.
    description : str, optional
        Description of the artifact (human readable).
    labels : list[str], optional
        List of labels.
    embedded : bool
        Flag to determine if the artifact specification must be embedded in
        the project specification.
    extensions : list[dict], optional
        List of extension dictionaries.
    **kwargs : dict
        Artifact specification keyword arguments.

    Returns
    -------
    ArtifactArtifact
        The registered artifact.

    Examples
    --------
    >>> obj = register_artifact(
    ...     project="my-project",
    ...     source="s3://my-bucket/models/my-model.pkl",
    ... )

    Notes
    -----
    Use :func:`log_artifact` for a local source that must be uploaded. That
    method combines artifact creation and upload, while this method only
    performs the creation step with ``source`` as the artifact path.
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
    **kwargs,
) -> ArtifactArtifact:
    """Create an artifact and upload a local source to its storage path.

    This high-level method combines the ``new_artifact`` and ``upload``
    operations. The source is read from the local filesystem, uploaded to the
    destination selected by ``path`` (or a generated destination), and the
    returned artifact contains the uploaded file metadata. To register a file
    that already exists in a supported store without uploading it, use
    :func:`register_artifact`.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    source : SourcesOrListOfSources
        Local artifact source path, or a list of local file paths.
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
    ArtifactArtifact
        Object instance.

    Examples
    --------
    >>> obj = log_artifact(project="my-project",
    >>>                    name="my-artifact",
    >>>                    source="./local-path")
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
        **kwargs,
    )
