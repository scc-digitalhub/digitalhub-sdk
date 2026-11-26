# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.versioned.builder import VersionedBuilder


class TriggerBuilder(VersionedBuilder):
    """
    Trigger builder.
    """

    ENTITY_TYPE = EntityTypes.TRIGGER.value
