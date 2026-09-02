from typing import ClassVar

import pytest

from digitalhub.entities._commons.utils import KindAction
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run.generic.builder import RunGenericBuilder
from digitalhub.utils.exceptions import EntityError


class InvalidRuntimeBuilder(RunBuilder):
    ENTITY_CLASS = RunGenericBuilder.ENTITY_CLASS
    ENTITY_SPEC_CLASS = RunGenericBuilder.ENTITY_SPEC_CLASS
    ENTITY_SPEC_VALIDATOR = RunGenericBuilder.ENTITY_SPEC_VALIDATOR
    ENTITY_STATUS_CLASS = RunGenericBuilder.ENTITY_STATUS_CLASS
    ENTITY_KIND = "invalid-runtime"


class ValidRuntimeBuilder(InvalidRuntimeBuilder):
    EXECUTABLE_KIND = "function-valid"
    TASKS_KINDS: ClassVar[list[KindAction]] = [KindAction("task-valid", "valid")]
    RUN_KINDS: ClassVar[list[KindAction]] = [KindAction("run-valid", "valid")]


def test_run_builder_rejects_incomplete_runtime_configuration() -> None:
    with pytest.raises(EntityError, match="EXECUTABLE_KIND must be set"):
        InvalidRuntimeBuilder()


def test_run_builder_accepts_complete_runtime_configuration() -> None:
    builder = ValidRuntimeBuilder()

    assert builder.get_executable_kind() == "function-valid"
    assert builder.get_action_from_task_kind("task-valid") == "valid"
    assert builder.get_task_kind_from_action("valid") == "task-valid"
    assert builder.get_run_kind_from_action("valid") == "run-valid"


def test_run_generic_builder_builds_entity_without_runtime_configuration() -> None:
    run = RunGenericBuilder().build(
        project="my-project",
        kind="python-run",
        name="run-name",
        uuid="run-id",
        task="task-id",
        local_execution=True,
        extensions=[{"key": "value"}],
    )

    assert run.project == "my-project"
    assert run.id == "run-id"
    assert run.kind == "python-run"
    assert run.spec.task == "task-id"
    assert run.spec.local_execution is True
    assert run.extensions == [{"key": "value"}]
