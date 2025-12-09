# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.automl.entity import TriggerAutoml
from digitalhub.entities.trigger.automl.spec import TriggerSpecAutoml, TriggerValidatorAutoml
from digitalhub.entities.trigger.automl.status import TriggerStatusAutoml


class TriggerAutomlBuilder(TriggerBuilder):
    """
    TriggerAutoml builder.
    """

    ENTITY_CLASS = TriggerAutoml
    ENTITY_SPEC_CLASS = TriggerSpecAutoml
    ENTITY_SPEC_VALIDATOR = TriggerValidatorAutoml
    ENTITY_STATUS_CLASS = TriggerStatusAutoml
    ENTITY_KIND = EntityKinds.TRIGGER_AUTOML.value
