# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.material.utils import kind_warning
from digitalhub.entities.model._base.crud import log_base_model, register_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.model.entity import ModelModel


def log_model(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> ModelModel:
    """
    Create and upload an object.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    source : SourcesOrListOfSources
        Model location on local path.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the model. If not provided, it's generated.
    version : str
        Version stored in entity metadata.
    description : str
        Model description.
    labels : list[str]
        Model labels.
    **kwargs : dict
        New model spec parameters.

    Returns
    -------
    ModelModel
        Object instance.

    Examples
    --------
    >>> obj = log_model(project="my-project",
    >>>                 name="my-model",
    >>>                 source="./local-path")
    """
    kind_warning(
        requested_kind=kwargs.pop("kind", None),
        set_kind=EntityKinds.MODEL_MODEL.value,
        entity_type=EntityTypes.MODEL.value,
    )
    return log_base_model(
        project=project,
        name=name,
        kind=EntityKinds.MODEL_MODEL.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        version=version,
        description=description,
        labels=labels,
        **kwargs,
    )


def register_model(
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
) -> ModelModel:
    """Register a model that already exists in a supported store."""
    return register_base_model(
        project=project,
        source=source,
        entity_kind=EntityKinds.MODEL_MODEL.value,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        **kwargs,
    )
