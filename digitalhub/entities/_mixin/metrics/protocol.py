# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol

from digitalhub.entities._mixin.unversioned.protocol import UnversionedEntityProtocol

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._commons.metrics import MetricType
    from digitalhub.entities._mixin.metrics.status import MetricsStatus


class MetricsEntityProtocol(UnversionedEntityProtocol, Protocol):
    status: MetricsStatus
    _entity_has_metrics: bool | None

    @property
    def metrics(self) -> dict: ...

    def log_metric(self, key: str, value: MetricType, overwrite: bool = False, single_value: bool = False) -> None: ...

    def log_metrics(self, metrics: dict[str, MetricType], overwrite: bool = False) -> None: ...

    def _update_attributes(self, obj: ContextEntity) -> None: ...
