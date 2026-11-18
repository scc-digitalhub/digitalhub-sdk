# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.generic.builder import GenericBuilder
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run.generic.entity import RunGeneric


class RunGenericBuilder(GenericBuilder, RunBuilder):
    """Builder for generic runs that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.RUN.value
    ENTITY_CLASS = RunGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
