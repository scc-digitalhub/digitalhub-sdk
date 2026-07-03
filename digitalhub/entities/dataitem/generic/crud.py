from __future__ import annotations

import typing

from digitalhub.entities.dataitem._base.crud import log_base_dataitem
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.generic.entity import DataitemGeneric


def log_generic_dataitem(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> DataitemGeneric:
    """Create and upload a dataitem of an unknown kind."""
    return log_base_dataitem(
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
