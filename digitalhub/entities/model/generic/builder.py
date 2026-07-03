from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.generic.entity import ModelGeneric


class ModelGenericBuilder(GenericBuilder, ModelBuilder):
    """Builder for generic models that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.MODEL.value
    ENTITY_CLASS = ModelGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
