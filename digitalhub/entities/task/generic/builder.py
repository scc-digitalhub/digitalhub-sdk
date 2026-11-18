# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.generic.builder import GenericBuilder
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.task.generic.entity import TaskGeneric


class TaskGenericBuilder(GenericBuilder, TaskBuilder):
    """Builder for generic tasks that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.TASK.value
    ENTITY_CLASS = TaskGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
