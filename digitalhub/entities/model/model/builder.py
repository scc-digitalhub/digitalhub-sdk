# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model._base.spec import ModelSpec
from digitalhub.entities.model._base.status import ModelStatus
from digitalhub.entities.model.model.entity import ModelModel


class ModelModelBuilder(ModelBuilder):
    """
    ModelModel builder.
    """

    ENTITY_CLASS = ModelModel
    ENTITY_SPEC_CLASS = ModelSpec
    ENTITY_STATUS_CLASS = ModelStatus
    ENTITY_KIND = EntityKinds.MODEL_MODEL.value
