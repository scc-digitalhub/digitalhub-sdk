# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.artifact._base.crud import log_base_artifact
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact


def log_generic_artifact(
    project: str,
    name: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
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
    **kwargs : dict
        New artifact spec parameters.

    Returns
    -------
    ArtifactArtifact
        Object instance.

    Examples
    --------
    >>> obj = log_generic_artifact(project="my-project",
    >>>                            name="my-generic-artifact",
    >>>                            source="./local-path")
    """
    warn("This method will become log_artifact in 0.16")
    return log_base_artifact(
        project=project,
        name=name,
        kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        **kwargs,
    )
