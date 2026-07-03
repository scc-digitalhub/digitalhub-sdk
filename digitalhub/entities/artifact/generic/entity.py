from __future__ import annotations

import typing

from digitalhub.entities._base.generic.entity import GenericEntity
from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.generic.spec import GenericSpec
    from digitalhub.entities._base.generic.status import GenericStatus


class ArtifactGeneric(VersionedEntity, GenericEntity):
    """Generic artifact entity that preserves runtime fields but does not expose download helpers."""

    ENTITY_TYPE = EntityTypes.ARTIFACT.value

    def __init__(self, *args, extensions: list[dict] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: GenericSpec
        self.status: GenericStatus
        self.extensions: list[dict] = extensions if extensions is not None else []

        self._obj_attr.extend(["extensions"])
