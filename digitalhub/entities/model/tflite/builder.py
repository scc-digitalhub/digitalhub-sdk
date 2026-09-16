# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.tflite.entity import ModelTflite
from digitalhub.entities.model.tflite.spec import ModelSpecTflite, ModelValidatorTflite
from digitalhub.entities.model.tflite.status import ModelStatusTflite


class ModelTfliteBuilder(ModelBuilder):
    """
    ModelTflite builder.
    """

    ENTITY_CLASS = ModelTflite
    ENTITY_SPEC_CLASS = ModelSpecTflite
    ENTITY_SPEC_VALIDATOR = ModelValidatorTflite
    ENTITY_STATUS_CLASS = ModelStatusTflite
    ENTITY_KIND = EntityKinds.MODEL_TFLITE.value
