# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities._mixin.material.spec import MaterialSpec
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem._base.status import DataitemStatus
from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant


class DataitemCroissantBuilder(DataitemBuilder):
    """
    DataitemCroissant builder.
    """

    ENTITY_CLASS = DataitemCroissant
    ENTITY_SPEC_CLASS = MaterialSpec
    ENTITY_STATUS_CLASS = DataitemStatus
    ENTITY_KIND = EntityKinds.DATAITEM_CROISSANT.value
