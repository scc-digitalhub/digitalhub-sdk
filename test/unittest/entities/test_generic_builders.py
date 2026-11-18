# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import inspect

import pytest

from digitalhub.entities.artifact._base.builder import ArtifactBuilder
from digitalhub.entities.artifact.generic.builder import ArtifactGenericBuilder
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.containerimage.generic.builder import ContainerimageGenericBuilder
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem.generic.builder import DataitemGenericBuilder
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.function.generic.builder import FunctionGenericBuilder
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model.generic.builder import ModelGenericBuilder
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run.generic.builder import RunGenericBuilder
from digitalhub.entities.secret._base.builder import SecretSecretBuilder
from digitalhub.entities.secret.generic.builder import SecretGenericBuilder
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.task.generic.builder import TaskGenericBuilder
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.generic.builder import TriggerGenericBuilder
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.entities.workflow.generic.builder import WorkflowGenericBuilder


@pytest.mark.parametrize(
    ("generic_builder", "base_builder"),
    [
        (ArtifactGenericBuilder, ArtifactBuilder),
        (DataitemGenericBuilder, DataitemBuilder),
        (ModelGenericBuilder, ModelBuilder),
        (ContainerimageGenericBuilder, ContainerimageBuilder),
        (FunctionGenericBuilder, FunctionBuilder),
        (WorkflowGenericBuilder, WorkflowBuilder),
        (TaskGenericBuilder, TaskBuilder),
        (RunGenericBuilder, RunBuilder),
        (SecretGenericBuilder, SecretSecretBuilder),
        (TriggerGenericBuilder, TriggerBuilder),
    ],
)
def test_generic_builders_inherit_public_build_contract(generic_builder, base_builder) -> None:
    assert issubclass(generic_builder, base_builder)
    assert inspect.signature(generic_builder.build) == inspect.signature(base_builder.build)
    assert "build" not in generic_builder.__dict__
    assert "_parse_dict" not in generic_builder.__dict__


def test_task_and_run_generic_builders_preserve_arbitrary_spec_fields() -> None:
    task = TaskGenericBuilder().build(
        project="project",
        kind="generic",
        labels=["task"],
        future_backend_field="task-value",
    )
    run = RunGenericBuilder().build(
        project="project",
        kind="generic",
        extensions=[{"name": "extension"}],
        future_backend_field="run-value",
    )

    assert task.spec.future_backend_field == "task-value"
    assert task.metadata.labels == ["task"]
    assert run.spec.future_backend_field == "run-value"
    assert run.extensions == [{"name": "extension"}]
