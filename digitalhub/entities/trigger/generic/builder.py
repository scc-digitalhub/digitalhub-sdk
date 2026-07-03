from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.generic.entity import TriggerGeneric


class TriggerGenericBuilder(GenericBuilder, TriggerBuilder):
    """Builder for generic triggers that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.TRIGGER.value
    ENTITY_CLASS = TriggerGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
