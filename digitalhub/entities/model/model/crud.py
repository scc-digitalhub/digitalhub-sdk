# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.crud import log_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.model.entity import ModelModel


def log_generic_model(
    project: str,
    name: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
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
    **kwargs : dict
        New model spec parameters.

    Returns
    -------
    ModelModel
        Object instance.

    Examples
    --------
    >>> obj = log_generic_model(project="my-project",
    >>>                         name="my-generic-model",
    >>>                         source="./local-path")
    """
    warn("This method will become log_model in 0.16")
    return log_base_model(
        project=project,
        name=name,
        kind=EntityKinds.MODEL_MODEL.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        **kwargs,
    )
