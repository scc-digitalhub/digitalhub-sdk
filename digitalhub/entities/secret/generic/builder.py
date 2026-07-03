from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.secret._base.builder import SecretSecretBuilder
from digitalhub.entities.secret.generic.entity import SecretGeneric


class SecretGenericBuilder(GenericBuilder, SecretSecretBuilder):
    """Builder for generic secrets that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.SECRET.value
    ENTITY_CLASS = SecretGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
