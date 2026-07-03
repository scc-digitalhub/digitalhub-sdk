from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem.generic.entity import DataitemGeneric


class DataitemGenericBuilder(GenericBuilder, DataitemBuilder):
    """Builder for generic dataitems that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.DATAITEM.value
    ENTITY_CLASS = DataitemGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
