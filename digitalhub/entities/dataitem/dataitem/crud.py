# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.material.utils import log_warning
from digitalhub.entities.dataitem._base.crud import log_base_dataitem
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.dataitem.entity import DataitemDataitem


def log_dataitem(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> DataitemDataitem:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    source : SourcesOrListOfSources
        Dataitem location on local path.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
    version : str
        Version stored in entity metadata.
    description : str
        Dataitem description.
    labels : list[str]
        Dataitem labels.
    **kwargs : dict
        New dataitem spec parameters.

    Returns
    -------
    DataitemDataitem
        Object instance.

    Examples
    --------
    >>> obj = log_dataitem(project="my-project",
                           name="my-dataitem-dataitem",
                           source="./local-path")
    """
    log_warning(
        requested_kind=kwargs.pop("kind", None),
        log_kind=EntityKinds.DATAITEM_DATAITEM.value,
        entity_type=EntityTypes.DATAITEM.value,
    )
    return log_base_dataitem(
        project=project,
        name=name,
        kind=EntityKinds.DATAITEM_DATAITEM.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )
