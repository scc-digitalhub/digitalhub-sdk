# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.model._base.spec import ModelSpec, ModelValidator
from digitalhub.entities.model._tvm.models import TensorSpec


class ModelSpecTvm(ModelSpec):
    """
    Shared base spec for TVM models (tvm-ir / tvm-so).
    """

    def __init__(
        self,
        path: str,
        framework: str | None = None,
        algorithm: str | None = None,
        parameters: dict | None = None,
        entry: str | None = None,
        inputs: list[dict] | None = None,
        outputs: list[dict] | None = None,
    ) -> None:
        super().__init__(path, framework, algorithm, parameters)
        self.entry = entry
        self.inputs = inputs
        self.outputs = outputs


class ModelValidatorTvm(ModelValidator):
    """
    Shared base validator for TVM models.
    """

    entry: str | None = None
    """Relax entry function (e.g. 'main')."""

    inputs: list[TensorSpec] | None = None
    """Input tensor signatures."""

    outputs: list[TensorSpec] | None = None
    """Output tensor signatures."""
