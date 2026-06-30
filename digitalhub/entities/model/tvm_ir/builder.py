# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model._tvm.status import ModelStatusTvm
from digitalhub.entities.model.tvm_ir.entity import ModelTvmIr
from digitalhub.entities.model.tvm_ir.spec import ModelSpecTvmIr, ModelValidatorTvmIr


class ModelTvmIrBuilder(ModelBuilder):
    """
    ModelTvmIr builder.
    """

    ENTITY_CLASS = ModelTvmIr
    ENTITY_SPEC_CLASS = ModelSpecTvmIr
    ENTITY_SPEC_VALIDATOR = ModelValidatorTvmIr
    ENTITY_STATUS_CLASS = ModelStatusTvm
    ENTITY_KIND = EntityKinds.MODEL_TVM_IR.value
