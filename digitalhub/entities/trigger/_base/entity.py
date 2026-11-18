# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.processors import control_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities.trigger._base.spec import TriggerSpec


class Trigger(ContextEntity, VersionedMixin):
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
        metadata,
        spec,
        status,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_versioned_identity(project, name, uuid, kind)
        self.spec: TriggerSpec
        self.status: Status

    def stop(self) -> None:
        """
        Stop trigger.
        """
        return control_processor.stop_entity(self.project, self.ENTITY_TYPE, self.id)
