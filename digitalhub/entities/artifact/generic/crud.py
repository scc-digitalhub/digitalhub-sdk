from __future__ import annotations

import typing

from digitalhub.entities.artifact._base.crud import log_base_artifact
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.generic.entity import ArtifactGeneric


def log_generic_artifact(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> ArtifactGeneric:
    """Create and upload an artifact of an unknown kind."""
    return log_base_artifact(
        project=project,
        name=name,
        kind=kind,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        **kwargs,
    )
