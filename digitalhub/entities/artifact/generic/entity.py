# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.generic.entity import GenericMixin
from digitalhub.entities._mixin.material.mixin import MaterialMixin
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities._mixin.generic.spec import GenericSpec
    from digitalhub.entities._mixin.generic.status import GenericStatus


class ArtifactGeneric(ContextEntity, VersionedMixin, MaterialMixin, GenericMixin):
    """Generic artifact entity that preserves runtime fields but does not expose download helpers."""

    ENTITY_TYPE = EntityTypes.ARTIFACT.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: GenericSpec,
        status: GenericStatus,
        extensions: list[dict] | None = None,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_versioned_identity(project, name, uuid, kind)

        self.spec: GenericSpec
        self.status: GenericStatus
        self._init_material_extensions(extensions)
