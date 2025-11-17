# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem.vectortable.entity import DataitemVectorTable
from digitalhub.entities.dataitem.vectortable.spec import DataitemSpecVectorTable, DataitemValidatorVectorTable
from digitalhub.entities.dataitem.vectortable.status import DataitemStatusVectorTable


class DataitemVectorTableBuilder(DataitemBuilder):
    """
    DataitemVectorTable builder.
    """

    ENTITY_CLASS = DataitemVectorTable
    ENTITY_SPEC_CLASS = DataitemSpecVectorTable
    ENTITY_SPEC_VALIDATOR = DataitemValidatorVectorTable
    ENTITY_STATUS_CLASS = DataitemStatusVectorTable
    ENTITY_KIND = EntityKinds.DATAITEM_VECTORTABLE.value
