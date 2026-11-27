# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._commons.metrics import MetricType, update_metrics, validate_metric_value
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import MetricsOptions
from digitalhub.stores.client.compiler.targets import ContextMetricTarget

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.metrics.protocol import MetricsEntityProtocol


class ContextEntityMetricsProcessor:
    def __init__(self, crud_processor: ContextEntityCRUDProcessor | None = None) -> None:
        self.crud_processor = ContextEntityCRUDProcessor() if crud_processor is None else crud_processor

    def get_metrics(self, obj: MetricsEntityProtocol) -> dict[str, MetricType]:
        """Return backend metrics when available, otherwise status metrics."""
        if obj._entity_has_metrics is True and obj.status.metrics:
            return obj.status.metrics
        backend_metrics = self.read_metrics_for_entity(obj)
        has_metrics = bool(backend_metrics) or bool(obj.status.metrics)
        obj._entity_has_metrics = has_metrics
        if not has_metrics:
            return {}
        if obj.status.metrics:
            return obj.status.metrics
        return backend_metrics

    def read_metrics_for_entity(self, obj: MetricsEntityProtocol) -> dict[str, MetricType]:
        return self.read_metrics(
            project=obj.project,
            entity_type=obj.ENTITY_TYPE,
            entity_id=obj.id,
        )

    def log_metric(
        self,
        obj: MetricsEntityProtocol,
        key: str,
        value: MetricType,
        overwrite: bool = False,
        single_value: bool = False,
    ) -> None:
        """Validate, aggregate, and persist one metric for an entity."""
        self._log_metric(obj, self.read_metrics_for_entity(obj), key, value, overwrite, single_value)

    def log_metrics(
        self,
        obj: MetricsEntityProtocol,
        metrics: dict[str, MetricType],
        overwrite: bool = False,
    ) -> None:
        """Persist multiple metrics while preserving append and overwrite semantics."""
        # Read once: each key is aggregated with its own stored value only.
        stored_metrics = self.read_metrics_for_entity(obj)
        has_metrics = bool(stored_metrics) or bool(obj.status.metrics)
        obj._entity_has_metrics = obj._entity_has_metrics or has_metrics
        for key, value in metrics.items():
            single_value = not isinstance(value, list) and (overwrite or not has_metrics or key not in stored_metrics)
            self._log_metric(obj, stored_metrics, key, value, overwrite, single_value)

    def _log_metric(
        self,
        obj: MetricsEntityProtocol,
        metrics: dict[str, MetricType],
        key: str,
        value: MetricType,
        overwrite: bool,
        single_value: bool,
    ) -> None:
        """Aggregate one metric with the stored ones and persist it."""
        validate_metric_value(value)
        if not metrics and not obj.status.metrics and not obj._entity_has_metrics:
            obj.status.metrics = {}
            obj._update_attributes(
                self.crud_processor.update_context_entity(obj.project, obj.ENTITY_TYPE, obj.id, obj.to_dict())
            )
        metrics = update_metrics(metrics, key, value, overwrite, single_value)
        self.update_metric(
            obj.project,
            obj.ENTITY_TYPE,
            obj.id,
            key,
            metrics[key],
        )
        obj._entity_has_metrics = True

    def read_metrics(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str | None = None,
        user: str | None = None,
    ) -> dict:
        return get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.METRICS_READ,
                target=ContextMetricTarget(project, entity_type, entity_id, metric_name),
                options=MetricsOptions(user=user),
            )
        )

    def update_metric(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: Any,
        user: str | None = None,
    ) -> None:
        get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.METRICS_UPDATE,
                target=ContextMetricTarget(project, entity_type, entity_id, metric_name),
                payload=metric_value,
                options=MetricsOptions(user=user),
            )
        )
