# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.material.mixin import MaterialMixin
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.spec import DataitemSpec
    from digitalhub.entities.dataitem._base.status import DataitemStatus


class Dataitem(ContextEntity, VersionedMixin, MaterialMixin):
    """
    A class representing a dataitem.
    """

    ENTITY_TYPE = EntityTypes.DATAITEM.value
    _obj_attr = (*ContextEntity._obj_attr, "extensions")

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata,
        spec,
        status,
        extensions: list[dict],
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_versioned_identity(project, name, uuid, kind)
        self.spec: DataitemSpec
        self.status: DataitemStatus
        self._init_material_extensions(extensions)
