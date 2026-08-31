# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.generic.entity import GenericMixin
from digitalhub.entities._mixin.metrics.mixin import MetricsMixin
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin
from digitalhub.entities.run._base.utils import init_run_extensions

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities._mixin.generic.spec import GenericSpec
    from digitalhub.entities._mixin.generic.status import GenericStatus


class RunGeneric(ContextEntity, UnversionedMixin, MetricsMixin, GenericMixin):
    """Generic run entity that preserves runtime fields without run-specific methods."""

    ENTITY_TYPE = EntityTypes.RUN.value
    _obj_attr = (*ContextEntity._obj_attr, "extensions")

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
        self._init_unversioned_identity(project, uuid, kind)
        self._init_metrics_state()

        self.spec: GenericSpec
        self.status: GenericStatus

        self.name = name
        init_run_extensions(self, extensions)
