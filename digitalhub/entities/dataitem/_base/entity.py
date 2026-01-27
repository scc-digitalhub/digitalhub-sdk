# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.material.entity import MaterialEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.dataitem._base.spec import DataitemSpec
    from digitalhub.entities.dataitem._base.status import DataitemStatus
    from digitalhub.entities._base.extensions.entity import Extension

class Dataitem(MaterialEntity):
    """
    A class representing a dataitem.
    """

    ENTITY_TYPE = EntityTypes.DATAITEM.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: DataitemSpec,
        status: DataitemStatus,
        extensions: list[Extension],
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, extensions, user)
        self.spec: DataitemSpec
        self.status: DataitemStatus
