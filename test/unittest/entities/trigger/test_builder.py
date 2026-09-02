import pytest

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.trigger.generic.builder import TriggerGenericBuilder
from digitalhub.entities.trigger.lifecycle.builder import TriggerLifecycleBuilder
from digitalhub.entities.trigger.scheduler.builder import TriggerSchedulerBuilder


@pytest.mark.parametrize(
    ("builder_class", "kind", "spec_kwargs", "expected_spec"),
    [
        (
            TriggerGenericBuilder,
            EntityKinds.GENERIC.value,
            {"event": "completed"},
            {"event": "completed"},
        ),
        (
            TriggerLifecycleBuilder,
            EntityKinds.TRIGGER_LIFECYCLE.value,
            {
                "task": "task-key",
                "template": {"state": "READY"},
                "key": "store://project/artifact/artifact/entity-id",
                "states": ["READY"],
            },
            {
                "task": "task-key",
                "template": {"state": "READY"},
                "key": "store://project/artifact/artifact/entity-id",
                "states": ["READY"],
            },
        ),
        (
            TriggerSchedulerBuilder,
            EntityKinds.TRIGGER_SCHEDULER.value,
            {
                "task": "task-key",
                "template": {"interval": "daily"},
                "schedule": "0 0 12 * * ?",
            },
            {
                "task": "task-key",
                "template": {"interval": "daily"},
                "schedule": "0 0 12 * * ?",
            },
        ),
    ],
)
def test_trigger_builders_build_entities(builder_class, kind, spec_kwargs, expected_spec) -> None:
    trigger = builder_class().build(
        project="my-project",
        name="trigger",
        kind=kind,
        uuid="trigger-id",
        **spec_kwargs,
    )

    assert trigger.project == "my-project"
    assert trigger.name == "trigger"
    assert trigger.id == "trigger-id"
    assert trigger.kind == kind
    for key, value in expected_spec.items():
        assert getattr(trigger.spec, key) == value
