# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import material_processor
from digitalhub.entities.dataitem._base.utils import build_log_kwargs
from digitalhub.utils.file_utils import eval_local_source

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.utils.types import SourcesOrListOfSources


def log_base_dataitem(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> Dataitem:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        return material_processor.log_material_entity(
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
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = log_base_dataitem(project="my-project",
    >>>                         name="my-dataitem",
    >>>                         kind="dataitem",
    >>>                         source="./local-path")
    """
    eval_local_source(source)
    kwargs = build_log_kwargs(
        project,
        name,
        entity_type=EntityTypes.DATAITEM.value,
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
        entity_type=EntityTypes.DATAITEM.value,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )
