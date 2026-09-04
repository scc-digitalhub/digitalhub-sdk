# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.crud import log_base_model, register_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.mlflow.entity import ModelMlflow
    from digitalhub.entities.model.mlflow.models import Dataset, Signature


def log_mlflow(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    version: str | None = None,
    framework: str | None = None,
    algorithm: str | None = None,
    parameters: dict | None = None,
    flavor: str | None = None,
    model_config: dict | None = None,
    input_datasets: list[Dataset] | None = None,
    signature: Signature | None = None,
    **kwargs,
) -> ModelMlflow:
    """
    Create and upload an MLflow model entity.

    Parameters
    ----------
    project : str
        Project name.
    name : str, optional
        Entity name. If omitted, it is inferred from ``source``.
    source : SourcesOrListOfSources
        Local model source path or paths.
    drop_existing : bool, default=False
        Whether to drop existing entity with the same name.
    path : str, optional
        Destination path. If omitted, it is generated.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    version : str, optional
        Entity version.
    framework : str, optional
        Model framework.
    algorithm : str, optional
        Model algorithm.
    parameters : dict, optional
        Model parameters.
    flavor : str, optional
        MLflow model flavor.
    model_config : dict, optional
        MLflow model configuration.
    input_datasets : list[Dataset], optional
        Datasets used as model inputs.
    signature : Signature, optional
        MLflow model signature.
    **kwargs : dict
        Additional model specification parameters.

    Returns
    -------
    ModelMlflow
        Created MLflow model entity with uploaded files.
    """
    return log_base_model(
        project=project,
        name=name,
        kind=EntityKinds.MODEL_MLFLOW.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        version=version,
        framework=framework,
        algorithm=algorithm,
        parameters=parameters,
        flavor=flavor,
        model_config=model_config,
        input_datasets=input_datasets,
        signature=signature,
        **kwargs,
    )


def register_mlflow(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    extensions: list[dict] | None = None,
    framework: str | None = None,
    algorithm: str | None = None,
    parameters: dict | None = None,
    flavor: str | None = None,
    model_config: dict | None = None,
    input_datasets: list[Dataset] | None = None,
    signature: Signature | None = None,
    **kwargs,
) -> ModelMlflow:
    """
    Register an MLflow model entity for an existing source.

    Parameters
    ----------
    project : str
        Project name.
    source : SourcesOrListOfSources
        Path or URI of the existing model.
    name : str, optional
        Entity name. If omitted, it is inferred from ``source``.
    uuid : str, optional
        Entity identifier.
    version : str, optional
        Entity version.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    embedded : bool, default=False
        Whether to embed the entity specification in the project specification.
    extensions : list[dict], optional
        Entity extensions.
    framework : str, optional
        Model framework.
    algorithm : str, optional
        Model algorithm.
    parameters : dict, optional
        Model parameters.
    flavor : str, optional
        MLflow model flavor.
    model_config : dict, optional
        MLflow model configuration.
    input_datasets : list[Dataset], optional
        Datasets used as model inputs.
    signature : Signature, optional
        MLflow model signature.
    **kwargs : dict
        Additional model specification parameters.

    Returns
    -------
    ModelMlflow
        Registered MLflow model entity.
    """
    return register_base_model(
        project=project,
        source=source,
        entity_kind=EntityKinds.MODEL_MLFLOW.value,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        framework=framework,
        algorithm=algorithm,
        parameters=parameters,
        flavor=flavor,
        model_config=model_config,
        input_datasets=input_datasets,
        signature=signature,
        **kwargs,
    )
