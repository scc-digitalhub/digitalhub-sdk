from __future__ import annotations

import typing

from digitalhub.entities._base.generic.entity import GenericEntity
from digitalhub.entities._base.unversioned.entity import UnversionedEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.generic.spec import GenericSpec
    from digitalhub.entities._base.generic.status import GenericStatus


class RunGeneric(UnversionedEntity, GenericEntity):
    """Generic run entity that preserves runtime fields without run-specific methods."""

    ENTITY_TYPE = EntityTypes.RUN.value

    def __init__(self, *args, extensions: list[dict] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: GenericSpec
        self.status: GenericStatus
        self.extensions: list[dict] = extensions if extensions is not None else []

        self._obj_attr.extend(["extensions"])
