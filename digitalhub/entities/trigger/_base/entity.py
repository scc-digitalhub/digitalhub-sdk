from __future__ import annotations

import typing

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.trigger._base.spec import TriggerSpec
    from digitalhub.entities.trigger._base.status import TriggerStatus


class Trigger(VersionedEntity):
    """
    A class representing a trigger.
    """

    ENTITY_TYPE = EntityTypes.TRIGGER.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TriggerSpec,
        status: TriggerStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)
        self.spec: TriggerSpec
        self.status: TriggerStatus
