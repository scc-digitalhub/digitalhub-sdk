# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.builders import generic_entity_builders
from digitalhub.factory.registry import registry

TriggerGenericBuilder = dict(generic_entity_builders)[EntityTypes.TRIGGER.value]


def _registered(kind: EntityKinds):
    return lambda: registry.get_entity_builder(kind.value)


@pytest.mark.parametrize(
    ("make_builder", "kind", "spec_kwargs", "expected_spec"),
    [
        (
            TriggerGenericBuilder,
            EntityKinds.GENERIC.value,
            {"event": "completed"},
            {"event": "completed"},
        ),
        (
            _registered(EntityKinds.TRIGGER_LIFECYCLE),
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
            _registered(EntityKinds.TRIGGER_SCHEDULER),
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
def test_trigger_builders_build_entities(make_builder, kind, spec_kwargs, expected_spec) -> None:
    trigger = make_builder().build(
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


def test_trigger_builder_routes_embedded_to_metadata() -> None:
    builder = registry.get_entity_builder(EntityKinds.TRIGGER_SCHEDULER.value)
    trigger = builder.build(
        project="project",
        name="trigger",
        kind=builder.ENTITY_KIND,
        embedded=True,
        task="task-key",
        template={"interval": "daily"},
        schedule="0 0 12 * * ?",
    )

    assert trigger.metadata.embedded is True
    assert "embedded" not in trigger.spec.to_dict()
