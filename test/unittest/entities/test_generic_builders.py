# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import inspect
from unittest.mock import Mock

import pytest

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.generic.builder import GenericBuilder
from digitalhub.entities._processors.context.control import ContextEntityControlProcessor
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities.artifact._base.builder import ArtifactBuilder
from digitalhub.entities.builders import generic_entity_builders
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.function._base.entity import Function
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run._base.entity import Run
from digitalhub.entities.run._base.processor import RunProcessor
from digitalhub.entities.secret._base.builder import SecretBuilder
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import BuilderError

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


def _unknown_run() -> Run:
    return entity_factory.build_entity_from_dict(
        {
            "project": "project",
            "id": "run-id",
            "kind": "unknown+run",
            "metadata": {"project": "project", "name": "run-id"},
            "spec": {"task": "unknown+job://project/task-id", "future_field": 1},
            "status": {"state": "RUNNING", "future_status": "x"},
        },
        entity_type=EntityTypes.RUN.value,
    )


def test_run_of_a_kind_without_runtime_keeps_the_backend_operations(monkeypatch) -> None:
    wait = Mock(side_effect=lambda run, **kwargs: run)
    logs = Mock(return_value=["line"])
    stop = Mock()
    monkeypatch.setattr(RunProcessor, "wait", wait)
    monkeypatch.setattr(RunProcessor, "read_logs", logs)
    monkeypatch.setattr(ContextEntityControlProcessor, "stop_entity", stop)

    run = _unknown_run()

    assert isinstance(run, Run)
    assert run.spec.future_field == 1
    assert run.status.future_status == "x"
    assert not run.local_execution()
    assert run.wait() is run
    assert run.logs() == ["line"]
    run.stop()
    stop.assert_called_once_with("project", EntityTypes.RUN.value, "run-id")


def _unknown_function() -> Function:
    return entity_factory.build_entity_from_dict(
        {
            "project": "project",
            "name": "function",
            "id": "function-id",
            "kind": "unknown",
            "metadata": {"project": "project", "name": "function"},
            "spec": {"source": {"code": "x"}},
        },
        entity_type=EntityTypes.FUNCTION.value,
    )


def test_function_of_a_kind_without_runtime_lists_its_runs(monkeypatch) -> None:
    list_runs = Mock(return_value=["run"])
    monkeypatch.setattr(ContextEntityExecutableProcessor, "list_executable_runs", list_runs)

    function = _unknown_function()

    assert isinstance(function, Function)
    assert function.list_runs() == ["run"]
    assert list_runs.call_args.args == (function,)


def test_function_of_a_kind_without_runtime_cannot_run() -> None:
    with pytest.raises(BuilderError, match="Kind 'unknown' not found: is the runtime that provides it installed?"):
        _unknown_function().run("job")
