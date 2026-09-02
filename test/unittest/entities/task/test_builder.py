from typing import ClassVar

import pytest

from digitalhub.entities._commons.utils import KindAction
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.task.generic.builder import TaskGenericBuilder
from digitalhub.utils.exceptions import EntityError


class InvalidRuntimeBuilder(TaskBuilder):
    ENTITY_CLASS = TaskGenericBuilder.ENTITY_CLASS
    ENTITY_SPEC_CLASS = TaskGenericBuilder.ENTITY_SPEC_CLASS
    ENTITY_SPEC_VALIDATOR = TaskGenericBuilder.ENTITY_SPEC_VALIDATOR
    ENTITY_STATUS_CLASS = TaskGenericBuilder.ENTITY_STATUS_CLASS
    ENTITY_KIND = "invalid-runtime"


class ValidRuntimeBuilder(InvalidRuntimeBuilder):
    EXECUTABLE_KIND = "function-valid"
    TASKS_KINDS: ClassVar[list[KindAction]] = [KindAction("task-valid", "valid")]
    RUN_KINDS: ClassVar[list[KindAction]] = [KindAction("run-valid", "valid")]


def test_task_builder_rejects_incomplete_runtime_configuration() -> None:
    with pytest.raises(EntityError, match="EXECUTABLE_KIND must be set"):
        InvalidRuntimeBuilder()


def test_task_builder_accepts_complete_runtime_configuration() -> None:
    builder = ValidRuntimeBuilder()

    assert builder.get_executable_kind() == "function-valid"
    assert builder.get_action_from_task_kind("task-valid") == "valid"
    assert builder.get_task_kind_from_action("valid") == "task-valid"
    assert builder.get_run_kind_from_action("valid") == "run-valid"


def test_task_generic_builder_builds_entity_without_runtime_configuration() -> None:
    task = TaskGenericBuilder().build(
        project="my-project",
        kind="python-task",
        uuid="task-id",
        labels=["batch"],
        function="function-key",
    )

    assert task.project == "my-project"
    assert task.id == "task-id"
    assert task.kind == "python-task"
    assert task.metadata.labels == ["batch"]
    assert task.spec.function == "function-key"
