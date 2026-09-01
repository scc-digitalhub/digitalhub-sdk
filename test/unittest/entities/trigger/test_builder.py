import pytest

from digitalhub.entities.trigger.generic.builder import TriggerGenericBuilder
from digitalhub.entities.trigger.lifecycle.builder import TriggerLifecycleBuilder
from digitalhub.entities.trigger.scheduler.builder import TriggerSchedulerBuilder


@pytest.mark.parametrize(
    "builder_class",
    [TriggerGenericBuilder, TriggerLifecycleBuilder, TriggerSchedulerBuilder],
)
def test_trigger_builders_are_configured(builder_class) -> None:
    builder_class()
