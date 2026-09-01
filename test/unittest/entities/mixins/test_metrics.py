from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._commons.metrics as metrics_utils
import digitalhub.entities._mixin.metrics.mixin as metrics_mixin
from digitalhub.entities._mixin.metrics.mixin import MetricsMixin


def test_metrics_rechecks_backend_after_negative_lookup() -> None:
    entity = MetricsMixin()
    entity.status = SimpleNamespace(metrics=None)
    entity._init_metrics_state()
    entity._read_metrics = Mock(return_value={})

    assert entity.metrics == {}

    entity._read_metrics.return_value = {"accuracy": 0.9}

    assert entity.metrics == {"accuracy": 0.9}


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, 1), (0.9, 0.9), ([1, 0.9], [1, 0.9])],
)
def test_validate_metric_value_accepts_numeric_values(value, expected) -> None:
    assert metrics_utils.validate_metric_value(value) == expected


@pytest.mark.parametrize("value", [None, "invalid", {"value": 1}, [1, "invalid"]])
def test_validate_metric_value_rejects_non_numeric_values(value) -> None:
    with pytest.raises(ValueError, match="Invalid metric value"):
        metrics_utils.validate_metric_value(value)


@pytest.mark.parametrize(
    ("metrics", "value", "overwrite", "single_value", "expected"),
    [
        ({}, 0.9, False, True, {"accuracy": 0.9}),
        ({"accuracy": 0.8}, 0.9, False, True, {"accuracy": 0.8}),
        ({"accuracy": 0.8}, 0.9, False, False, {"accuracy": [0.8, 0.9]}),
        ({"accuracy": [0.8]}, 0.9, False, False, {"accuracy": [0.8, 0.9]}),
        ({"accuracy": [0.8]}, [0.9], False, False, {"accuracy": [0.8, 0.9]}),
        ({"accuracy": 0.8}, 0.9, True, True, {"accuracy": 0.9}),
    ],
)
def test_update_metrics_handles_scalar_and_list_values(
    metrics: dict,
    value,
    overwrite: bool,
    single_value: bool,
    expected: dict,
) -> None:
    assert metrics_utils.update_metrics(metrics, "accuracy", value, overwrite, single_value) == expected


def test_log_metric_initializes_status_and_updates_backend(monkeypatch) -> None:
    entity = MetricsMixin()
    entity.project = "project"
    entity.ENTITY_TYPE = "artifact"
    entity.id = "entity-id"
    entity.status = SimpleNamespace(metrics=None)
    entity.save = Mock()
    entity._init_metrics_state()
    entity._read_metrics = Mock(return_value={})
    update_metric = Mock()
    monkeypatch.setattr(metrics_mixin.metrics_processor, "update_metric", update_metric)

    entity.log_metric("accuracy", 0.9)

    assert entity.status.metrics == {}
    entity.save.assert_called_once_with(update=True)
    update_metric.assert_called_once_with("project", "artifact", "entity-id", "accuracy", [0.9])


def test_log_metric_appends_to_existing_backend_metric(monkeypatch) -> None:
    entity = MetricsMixin()
    entity.project = "project"
    entity.ENTITY_TYPE = "artifact"
    entity.id = "entity-id"
    entity.status = SimpleNamespace(metrics=None)
    entity._init_metrics_state()
    entity._read_metrics = Mock(return_value={"accuracy": [0.8]})
    update_metric = Mock()
    monkeypatch.setattr(metrics_mixin.metrics_processor, "update_metric", update_metric)

    entity.log_metric("accuracy", 0.9)

    update_metric.assert_called_once_with("project", "artifact", "entity-id", "accuracy", [0.8, 0.9])
