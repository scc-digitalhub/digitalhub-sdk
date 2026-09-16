# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities.model._base.spec import ModelSpec, ModelValidator
from digitalhub.entities.model.tvm.models import TensorSpec


class ModelSpecOnnx(ModelSpec):
    """
    ModelSpecOnnx specifications. Source model in ONNX format, e.g. the input of tvm+build.
    """

    def __init__(
        self,
        path: str,
        framework: str | None = None,
        algorithm: str | None = None,
        parameters: dict | None = None,
        inputs: list[dict] | None = None,
        outputs: list[dict] | None = None,
        opset: int | None = None,
    ) -> None:
        super().__init__(path, framework, algorithm, parameters)
        self.inputs = inputs
        self.outputs = outputs
        self.opset = opset


class ModelValidatorOnnx(ModelValidator):
    """
    ModelValidatorOnnx validator.
    """

    inputs: list[TensorSpec] | None = None
    """Input tensors as declared by the model (name, dtype, shape, quantization)."""

    outputs: list[TensorSpec] | None = None
    """Output tensors as declared by the model."""

    opset: int | None = Field(default=None, ge=1)
    """Default ONNX operator set version the model was exported with (e.g. 17)."""
