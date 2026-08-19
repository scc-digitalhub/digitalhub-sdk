# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.artifact._base.crud import log_base_artifact
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.generic.entity import ArtifactGeneric


def log_generic_artifact(
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
) -> ArtifactGeneric:
    """Create and upload an artifact of an unknown kind.

    version : str
        Version stored in entity metadata.
    """
    return log_base_artifact(
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
