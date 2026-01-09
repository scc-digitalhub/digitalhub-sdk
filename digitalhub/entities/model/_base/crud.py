# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.processors import context_processor
from digitalhub.entities.model._base.utils import build_log_kwargs
from digitalhub.utils.file_utils import eval_local_source

if typing.TYPE_CHECKING:
    from digitalhub.entities.model._base.entity import Model
    from digitalhub.utils.types import SourcesOrListOfSources


def log_base_model(
    project: str,
    name: str,
    kind: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    **kwargs,
) -> Model:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    kind : str
        Kind the object.
    source : SourcesOrListOfSources
        Model location on local path.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the model. If not provided, it's generated.
    **kwargs : dict
        New model spec parameters.

    Returns
    -------
    Model
        Object instance.

    Examples
    --------
    >>> obj = log_base_model(project="my-project",
    >>>                      name="my-model",
    >>>                      kind="model",
    >>>                      source="./local-path")
    """
    eval_local_source(source)
    kwargs = build_log_kwargs(
        project,
        name,
        entity_type=EntityTypes.MODEL.value,
        source=source,
        path=path,
        **kwargs,
    )
    return context_processor.log_material_entity(
        source=source,
        project=project,
        name=name,
        kind=kind,
        drop_existing=drop_existing,
        entity_type=EntityTypes.MODEL.value,
        **kwargs,
    )
