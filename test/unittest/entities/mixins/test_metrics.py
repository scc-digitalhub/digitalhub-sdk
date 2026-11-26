# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._commons.metrics as metrics_utils
from digitalhub.entities._mixin.metrics.mixin import MetricsMixin
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.context.metrics import ContextEntityMetricsProcessor


def test_metrics_rechecks_backend_after_negative_lookup(monkeypatch) -> None:
    entity = MetricsMixin()
    entity.project = "project"
    entity.ENTITY_TYPE = "artifact"
    entity.id = "entity-id"
    entity.status = SimpleNamespace(metrics=None)
    entity._init_metrics_state()
    read_metrics = Mock(return_value={})
    monkeypatch.setattr(ContextEntityMetricsProcessor, "read_metrics", read_metrics)

    assert entity.metrics == {}

    read_metrics.return_value = {"accuracy": 0.9}

    assert entity.metrics == {"accuracy": 0.9}


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, 1), (0.9, 0.9), ([1, 0.9], [1, 0.9])],
)
def test_validate_metric_value_accepts_numeric_values(value, expected) -> None:
    assert metrics_utils.validate_metric_value(value) == expected


@pytest.mark.parametrize("value", [None, "invalid", {"value": 1}, [1, "invalid"], True, False, [1, True]])
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
        ({"accuracy": 0.8}, [0.9, 1.0], False, False, {"accuracy": [0.8, 0.9, 1.0]}),
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
    entity.update = Mock()
    entity.to_dict = Mock(return_value={"id": "entity-id"})
    entity._update_attributes = Mock()
    update_entity = Mock()
    monkeypatch.setattr(ContextEntityCRUDProcessor, "update_context_entity", update_entity)
    entity._init_metrics_state()
    backend_metrics = {}

    def read_metrics(**kwargs):
        return backend_metrics.copy()

    def update_metric(project, entity_type, entity_id, key, value):
        backend_metrics[key] = value

    monkeypatch.setattr(ContextEntityMetricsProcessor, "read_metrics", staticmethod(read_metrics))
    monkeypatch.setattr(ContextEntityMetricsProcessor, "update_metric", staticmethod(update_metric))

    entity.log_metric("accuracy", 0.9)

    assert entity.status.metrics == {}
    assert entity.metrics == {"accuracy": [0.9]}
    update_entity.assert_called_once_with("project", "artifact", "entity-id", {"id": "entity-id"})
    entity._update_attributes.assert_called_once_with(update_entity.return_value)
    entity.update.assert_not_called()


def test_log_metric_appends_to_existing_backend_metric(monkeypatch) -> None:
    entity = MetricsMixin()
    entity.project = "project"
    entity.ENTITY_TYPE = "artifact"
    entity.id = "entity-id"
    entity.status = SimpleNamespace(metrics=None)
    entity._init_metrics_state()
    backend_metrics = {"accuracy": [0.8]}

    def read_metrics(**kwargs):
        return backend_metrics.copy()

    def update_metric(project, entity_type, entity_id, key, value):
        backend_metrics[key] = value

    monkeypatch.setattr(ContextEntityMetricsProcessor, "read_metrics", staticmethod(read_metrics))
    monkeypatch.setattr(ContextEntityMetricsProcessor, "update_metric", staticmethod(update_metric))

    entity.log_metric("accuracy", 0.9)

    assert entity.metrics == {"accuracy": [0.8, 0.9]}
