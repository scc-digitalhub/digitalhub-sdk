# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.onnx.entity import ModelOnnx
from digitalhub.entities.model.onnx.spec import ModelSpecOnnx, ModelValidatorOnnx
from digitalhub.entities.model.onnx.status import ModelStatusOnnx


class ModelOnnxBuilder(ModelBuilder):
    """
    ModelOnnx builder.
    """

    ENTITY_CLASS = ModelOnnx
    ENTITY_SPEC_CLASS = ModelSpecOnnx
    ENTITY_SPEC_VALIDATOR = ModelValidatorOnnx
    ENTITY_STATUS_CLASS = ModelStatusOnnx
    ENTITY_KIND = EntityKinds.MODEL_ONNX.value
