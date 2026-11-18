# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.status import Status
from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.scheduler.entity import TriggerScheduler
from digitalhub.entities.trigger.scheduler.spec import TriggerSpecScheduler


class TriggerSchedulerBuilder(TriggerBuilder):
    """
    TriggerScheduler builder.
    """

    ENTITY_CLASS = TriggerScheduler
    ENTITY_SPEC_CLASS = TriggerSpecScheduler
    ENTITY_STATUS_CLASS = Status
    ENTITY_KIND = EntityKinds.TRIGGER_SCHEDULER.value
