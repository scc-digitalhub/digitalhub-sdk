# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.status import Status
from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.lifecycle.entity import TriggerLifecycle
from digitalhub.entities.trigger.lifecycle.spec import TriggerSpecLifecycle


class TriggerLifecycleBuilder(TriggerBuilder):
    """
    TriggerLifecycle builder.
    """

    ENTITY_CLASS = TriggerLifecycle
    ENTITY_SPEC_CLASS = TriggerSpecLifecycle
    ENTITY_STATUS_CLASS = Status
    ENTITY_KIND = EntityKinds.TRIGGER_LIFECYCLE.value
