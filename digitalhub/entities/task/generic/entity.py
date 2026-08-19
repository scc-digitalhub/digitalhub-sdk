# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.generic.entity import GenericMixin
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities._mixin.generic.spec import GenericSpec
    from digitalhub.entities._mixin.generic.status import GenericStatus


class TaskGeneric(ContextEntity, UnversionedMixin, GenericMixin):
    """Generic task entity that preserves runtime fields without task-specific methods."""

    ENTITY_TYPE = EntityTypes.TASK.value

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: GenericSpec,
        status: GenericStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_unversioned_identity(project, uuid, kind)

        self.spec: GenericSpec
        self.status: GenericStatus
