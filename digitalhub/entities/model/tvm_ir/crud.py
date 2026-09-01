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


def log_tvm_ir(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> ModelTvmIr:
    """
    Create and upload a tvm-ir model (Relax IR produced by tvm+build).

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
    description : str
        Model description.
    labels : list[str]
        Model labels.
    **kwargs : dict
        New model spec parameters (entry, inputs, outputs, source_format,
        keep_params_in_input, framework, algorithm, ...).

    Returns
    -------
    ModelTvmIr
        Object instance.

    Examples
    --------
    >>> obj = log_tvm_ir(project="my-project",
    >>>                  name="my-ir-model",
    >>>                  source="./out",
    >>>                  source_format="onnx")
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
    **kwargs,
) -> ModelTvmIr:
    """Register a TVM IR model that already exists in a supported store."""
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
        **kwargs,
    )
