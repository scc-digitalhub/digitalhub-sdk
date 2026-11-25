# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import inspect

import pytest

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.generic.builder import GenericBuilder
from digitalhub.entities.artifact._base.builder import ArtifactBuilder
from digitalhub.entities.builders import generic_entity_builders
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.secret._base.builder import SecretBuilder
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.workflow._base.builder import WorkflowBuilder

GENERIC_BUILDERS = dict(generic_entity_builders)


@pytest.mark.parametrize(
    ("entity_type", "base_builder"),
    [
        (EntityTypes.ARTIFACT, ArtifactBuilder),
        (EntityTypes.DATAITEM, DataitemBuilder),
        (EntityTypes.MODEL, ModelBuilder),
        (EntityTypes.CONTAINERIMAGE, ContainerimageBuilder),
        (EntityTypes.FUNCTION, FunctionBuilder),
        (EntityTypes.WORKFLOW, WorkflowBuilder),
        (EntityTypes.TASK, TaskBuilder),
        (EntityTypes.RUN, RunBuilder),
        (EntityTypes.SECRET, SecretBuilder),
        (EntityTypes.TRIGGER, TriggerBuilder),
    ],
)
def test_generic_builders_inherit_public_build_contract(entity_type, base_builder) -> None:
    generic_builder = GENERIC_BUILDERS[entity_type.value]

    assert generic_builder.__bases__ == (GenericBuilder, base_builder)
    assert generic_builder.ENTITY_KIND == EntityKinds.GENERIC.value
    assert inspect.signature(generic_builder.build) == inspect.signature(base_builder.build)


def test_task_and_run_generic_builders_preserve_arbitrary_spec_fields() -> None:
    task = GENERIC_BUILDERS[EntityTypes.TASK.value]().build(
        project="project",
        kind="generic",
        labels=["task"],
        future_backend_field="task-value",
    )
    run = GENERIC_BUILDERS[EntityTypes.RUN.value]().build(
        project="project",
        kind="generic",
        extensions=[{"name": "extension"}],
        future_backend_field="run-value",
    )

    assert task.spec.future_backend_field == "task-value"
    assert task.metadata.labels == ["task"]
    assert run.spec.future_backend_field == "run-value"
    assert run.extensions == [{"name": "extension"}]
