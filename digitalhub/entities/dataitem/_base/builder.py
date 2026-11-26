# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.material.builder import MaterialBuilder


class DataitemBuilder(MaterialBuilder):
    """
    Dataitem builder.
    """

    ENTITY_TYPE = EntityTypes.DATAITEM.value
