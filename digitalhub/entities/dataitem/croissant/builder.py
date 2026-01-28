# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant
from digitalhub.entities.dataitem.croissant.spec import DataitemSpecCroissant, DataitemValidatorCroissant
from digitalhub.entities.dataitem.croissant.status import DataitemStatusCroissant


class DataitemCroissantBuilder(DataitemBuilder):
    """
    DataitemCroissant builder.
    """

    ENTITY_CLASS = DataitemCroissant
    ENTITY_SPEC_CLASS = DataitemSpecCroissant
    ENTITY_SPEC_VALIDATOR = DataitemValidatorCroissant
    ENTITY_STATUS_CLASS = DataitemStatusCroissant
    ENTITY_KIND = EntityKinds.DATAITEM_CROISSANT.value
