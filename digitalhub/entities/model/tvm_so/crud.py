# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.crud import log_base_model
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.tvm_so.entity import ModelTvmSo


def log_tvm_so(
    project: str,
    name: str,
    source: SourcesOrListOfSources,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    **kwargs,
) -> ModelTvmSo:
    """
    Create and upload a tvm-so model (compiled model.so produced by tvm+compile).

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
        New model spec parameters (entry, inputs, outputs, target, opt_level,
        manifest, framework, algorithm, ...).

    Returns
    -------
    ModelTvmSo
        Object instance.

    Examples
    --------
    >>> obj = log_tvm_so(project="my-project",
    >>>                  name="my-so-model",
    >>>                  source="./out",
    >>>                  target="llvm -mcpu=x86-64-v2")
    """
    return log_base_model(
        project=project,
        name=name,
        kind=EntityKinds.MODEL_TVM_SO.value,
        source=source,
        drop_existing=drop_existing,
        path=path,
        description=description,
        labels=labels,
        **kwargs,
    )
