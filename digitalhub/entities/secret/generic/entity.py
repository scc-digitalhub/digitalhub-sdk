from __future__ import annotations

import typing

from digitalhub.entities._base.generic.entity import GenericEntity
from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.generic.spec import GenericSpec
    from digitalhub.entities._base.generic.status import GenericStatus


class SecretGeneric(VersionedEntity, GenericEntity):
    """Generic secret entity that preserves runtime fields without secret-specific methods."""

    ENTITY_TYPE = EntityTypes.SECRET.value

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: GenericSpec
        self.status: GenericStatus
