from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.containerimage.generic.entity import ContainerimageGeneric


class ContainerimageGenericBuilder(GenericBuilder, ContainerimageBuilder):
    """Builder for generic container images that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.CONTAINERIMAGE.value
    ENTITY_CLASS = ContainerimageGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
