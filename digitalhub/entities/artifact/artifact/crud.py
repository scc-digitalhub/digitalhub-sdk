# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.material.utils import log_warning
from digitalhub.entities.artifact._base.crud import log_base_artifact
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact


def log_artifact(
    project: str,
    name: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> ArtifactArtifact:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
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
    ArtifactArtifact
        Object instance.

    Examples
    --------
    >>> obj = log_artifact(project="my-project",
    >>>                    name="my-artifact",
    >>>                    source="./local-path")
    """
    log_warning(
        requested_kind=kwargs.pop("kind", None),
        log_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
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
