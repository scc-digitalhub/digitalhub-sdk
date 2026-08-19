# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations


class ContextEntityMetricsProcessor:
    def read_metrics(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str | None = None,
        **kwargs,
    ) -> dict:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.METRICS.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
        )
        return context.client.read_object(api, **kwargs)

    def update_metric(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        metric_value: Any,
        **kwargs,
    ) -> None:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.METRICS.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
        )
        context.client.update_object(api, metric_value, **kwargs)
