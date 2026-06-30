# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model._tvm.status import ModelStatusTvm
from digitalhub.entities.model.tvm_so.entity import ModelTvmSo
from digitalhub.entities.model.tvm_so.spec import ModelSpecTvmSo, ModelValidatorTvmSo


class ModelTvmSoBuilder(ModelBuilder):
    """
    ModelTvmSo builder.
    """

    ENTITY_CLASS = ModelTvmSo
    ENTITY_SPEC_CLASS = ModelSpecTvmSo
    ENTITY_SPEC_VALIDATOR = ModelValidatorTvmSo
    ENTITY_STATUS_CLASS = ModelStatusTvm
    ENTITY_KIND = EntityKinds.MODEL_TVM_SO.value
