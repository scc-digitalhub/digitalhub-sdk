# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.material.mixin import MaterialMixin
from digitalhub.entities._mixin.metrics.mixin import MetricsMixin
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin

if typing.TYPE_CHECKING:
    from digitalhub.entities.model._base.spec import ModelSpec
    from digitalhub.entities.model._base.status import ModelStatus


class Model(ContextEntity, VersionedMixin, MaterialMixin, MetricsMixin):
    """
    A class representing a model.
    """

    ENTITY_TYPE = EntityTypes.MODEL.value
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
        self._init_metrics_state()
        self.spec: ModelSpec
        self.status: ModelStatus
        self._init_material_extensions(extensions)
