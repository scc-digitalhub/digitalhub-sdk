# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.crud import log_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.mlflow.entity import ModelMlflow


def log_mlflow(
    project: str,
    name: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    **kwargs,
) -> ModelMlflow:
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
    ModelMlflow
        Object instance.

    Examples
    --------
    >>> obj = log_mlflow(project="my-project",
    >>>                        name="my-mlflow-model",
    >>>                        source="./local-path")
    """
    return log_base_model(
        project=project,
        name=name,
        kind=EntityKinds.MODEL_MLFLOW.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        **kwargs,
    )
