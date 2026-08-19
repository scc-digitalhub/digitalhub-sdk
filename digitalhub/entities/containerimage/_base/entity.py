# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin

if typing.TYPE_CHECKING:
    from digitalhub.entities.containerimage._base.spec import ContainerimageSpec
    from digitalhub.entities.containerimage._base.status import ContainerimageStatus


class Containerimage(ContextEntity, VersionedMixin):
    """
    A class representing a image.
    """

    ENTITY_TYPE = EntityTypes.CONTAINERIMAGE.value

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
        self.spec: ContainerimageSpec
        self.status: ContainerimageStatus
