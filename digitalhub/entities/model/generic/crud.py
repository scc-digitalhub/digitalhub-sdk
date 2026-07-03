from __future__ import annotations

import typing

from digitalhub.entities.model._base.crud import log_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.generic.entity import ModelGeneric


def log_generic_model(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> ModelGeneric:
    """Create and upload a model of an unknown kind."""
    return log_base_model(
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
