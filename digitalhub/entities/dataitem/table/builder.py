# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem._base.status import DataitemStatus
from digitalhub.entities.dataitem.table.entity import DataitemTable
from digitalhub.entities.dataitem.table.spec import DataitemSpecTable


class DataitemTableBuilder(DataitemBuilder):
    """
    DataitemTable builder.
    """

    ENTITY_CLASS = DataitemTable
    ENTITY_SPEC_CLASS = DataitemSpecTable
    ENTITY_STATUS_CLASS = DataitemStatus
    ENTITY_KIND = EntityKinds.DATAITEM_TABLE.value
