# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.model._base.spec import ModelSpec, ModelValidator
from digitalhub.entities.model.tvm.models import TensorSpec


class ModelSpecTflite(ModelSpec):
    """
    ModelSpecTflite specifications. Source model in TFLite format, e.g. the input of tvm+build.
    """

    def __init__(
        self,
        path: str,
        framework: str | None = None,
        algorithm: str | None = None,
        parameters: dict | None = None,
        inputs: list[dict] | None = None,
        outputs: list[dict] | None = None,
    ) -> None:
        super().__init__(path, framework, algorithm, parameters)
        self.inputs = inputs
        self.outputs = outputs


class ModelValidatorTflite(ModelValidator):
    """
    ModelValidatorTflite validator.
    """

    inputs: list[TensorSpec] | None = None
    """Input tensors as declared by the model (name, dtype, shape, quantization)."""

    outputs: list[TensorSpec] | None = None
    """Output tensors as declared by the model."""
