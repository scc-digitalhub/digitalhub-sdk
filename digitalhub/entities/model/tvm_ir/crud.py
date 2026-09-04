# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.crud import log_base_model, register_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.tvm_ir.entity import ModelTvmIr
    from digitalhub.entities.model.tvm_ir.spec import TvmSourceFormat


def log_tvm_ir(
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
    entry: str | None = None,
    inputs: list[dict] | None = None,
    outputs: list[dict] | None = None,
    source_format: TvmSourceFormat | None = None,
    keep_params_in_input: bool | None = None,
    sanitize_input_names: bool | None = None,
    **kwargs,
) -> ModelTvmIr:
    """
    Create and upload a TVM IR model entity.

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
    entry : str, optional
        Relax entry function.
    inputs : list[dict], optional
        Input tensor signatures.
    outputs : list[dict], optional
        Output tensor signatures.
    source_format : TvmSourceFormat, optional
        Source model format.
    keep_params_in_input : bool, optional
        Whether weights are kept as input variables.
    sanitize_input_names : bool, optional
        Whether input names were sanitized by the ONNX frontend.
    **kwargs : dict
        Additional model specification parameters.

    Returns
    -------
    ModelTvmIr
        Created TVM IR model entity with uploaded files.
    """
    return log_base_model(
        project=project,
        name=name,
        kind=EntityKinds.MODEL_TVM_IR.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        version=version,
        framework=framework,
        algorithm=algorithm,
        parameters=parameters,
        entry=entry,
        inputs=inputs,
        outputs=outputs,
        source_format=source_format,
        keep_params_in_input=keep_params_in_input,
        sanitize_input_names=sanitize_input_names,
        **kwargs,
    )


def register_tvm_ir(
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
    entry: str | None = None,
    inputs: list[dict] | None = None,
    outputs: list[dict] | None = None,
    source_format: TvmSourceFormat | None = None,
    keep_params_in_input: bool | None = None,
    sanitize_input_names: bool | None = None,
    **kwargs,
) -> ModelTvmIr:
    """
    Register a TVM IR model entity for an existing source.

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
    entry : str, optional
        Relax entry function.
    inputs : list[dict], optional
        Input tensor signatures.
    outputs : list[dict], optional
        Output tensor signatures.
    source_format : TvmSourceFormat, optional
        Source model format.
    keep_params_in_input : bool, optional
        Whether weights are kept as input variables.
    sanitize_input_names : bool, optional
        Whether input names were sanitized by the ONNX frontend.
    **kwargs : dict
        Additional model specification parameters.

    Returns
    -------
    ModelTvmIr
        Registered TVM IR model entity.
    """
    return register_base_model(
        project=project,
        source=source,
        entity_kind=EntityKinds.MODEL_TVM_IR.value,
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
        entry=entry,
        inputs=inputs,
        outputs=outputs,
        source_format=source_format,
        keep_params_in_input=keep_params_in_input,
        sanitize_input_names=sanitize_input_names,
        **kwargs,
    )
