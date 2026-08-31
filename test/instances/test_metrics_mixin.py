from types import SimpleNamespace
from unittest.mock import Mock

from digitalhub.entities._mixin.metrics.mixin import MetricsMixin


def test_metrics_rechecks_backend_after_negative_lookup() -> None:
    entity = MetricsMixin()
    entity.status = SimpleNamespace(metrics=None)
    entity._init_metrics_state()
    entity._read_metrics = Mock(return_value={})

    assert entity.metrics == {}

    entity._read_metrics.return_value = {"accuracy": 0.9}

    assert entity.metrics == {"accuracy": 0.9}
