# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import MetricsOptions
from digitalhub.stores.client.compiler.targets import ContextMetricTarget


class ContextEntityMetricsProcessor:
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
