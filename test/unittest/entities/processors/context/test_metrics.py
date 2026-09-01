from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.metrics as metrics_module
from digitalhub.entities._processors.context.metrics import ContextEntityMetricsProcessor
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    api = object()
    client.build_api.return_value = api
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, api


def test_read_metrics_builds_api_and_reads_object(monkeypatch) -> None:
    context, client, api = _context()
    client.read_object.return_value = {"accuracy": 0.9}
    monkeypatch.setattr(metrics_module, "get_context", Mock(return_value=context))

    result = ContextEntityMetricsProcessor().read_metrics(
        "project",
        "run",
        "run-id",
        metric_name="accuracy",
        user="user",
    )

    assert result == {"accuracy": 0.9}
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.METRICS.value,
        project="context-project",
        entity_type="run",
        entity_id="run-id",
        metric_name="accuracy",
    )
    client.read_object.assert_called_once_with(api, user="user")


def test_update_metric_builds_api_and_updates_object(monkeypatch) -> None:
    context, client, api = _context()
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
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.METRICS.value,
        project="context-project",
        entity_type="run",
        entity_id="run-id",
        metric_name="accuracy",
    )
    client.update_object.assert_called_once_with(api, [0.8, 0.9], user="user")
