# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.metrics as metrics_module
from digitalhub.entities._processors.context.metrics import ContextEntityMetricsProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import MetricsOptions
from digitalhub.stores.client.compiler.targets import ContextMetricTarget


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, object()


def test_read_metrics_uses_backend_operation_request(monkeypatch) -> None:
    context, client, _ = _context()
    client.execute.return_value = {"accuracy": 0.9}
    monkeypatch.setattr(metrics_module, "get_context", Mock(return_value=context))

    result = ContextEntityMetricsProcessor().read_metrics(
        "project",
        "run",
        "run-id",
        metric_name="accuracy",
        user="user",
    )

    assert result == {"accuracy": 0.9}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.METRICS_READ,
            target=ContextMetricTarget("project", "run", "run-id", "accuracy"),
            options=MetricsOptions(user="user"),
        )
    )


def test_update_metric_uses_backend_operation_request(monkeypatch) -> None:
    context, client, _ = _context()
    monkeypatch.setattr(metrics_module, "get_context", Mock(return_value=context))

    result = ContextEntityMetricsProcessor().update_metric(
        "project",
        "run",
        "run-id",
        "accuracy",
        [0.8, 0.9],
        user="user",
    )

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.METRICS_UPDATE,
            target=ContextMetricTarget("project", "run", "run-id", "accuracy"),
            payload=[0.8, 0.9],
            options=MetricsOptions(user="user"),
        )
    )
