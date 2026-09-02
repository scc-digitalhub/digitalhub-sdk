from typing import ClassVar

import pytest

from digitalhub.entities._commons.utils import KindAction
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.function.generic.builder import FunctionGenericBuilder
from digitalhub.utils.exceptions import EntityError


class InvalidRuntimeBuilder(FunctionBuilder):
    ENTITY_CLASS = FunctionGenericBuilder.ENTITY_CLASS
    ENTITY_SPEC_CLASS = FunctionGenericBuilder.ENTITY_SPEC_CLASS
    ENTITY_SPEC_VALIDATOR = FunctionGenericBuilder.ENTITY_SPEC_VALIDATOR
    ENTITY_STATUS_CLASS = FunctionGenericBuilder.ENTITY_STATUS_CLASS
    ENTITY_KIND = "invalid-runtime"


class ValidRuntimeBuilder(InvalidRuntimeBuilder):
    EXECUTABLE_KIND = "function-valid"
    TASKS_KINDS: ClassVar[list[KindAction]] = [KindAction("task-valid", "valid")]
    RUN_KINDS: ClassVar[list[KindAction]] = [KindAction("run-valid", "valid")]


def test_entity_builder_rejects_incomplete_runtime_configuration() -> None:
    with pytest.raises(EntityError, match="EXECUTABLE_KIND must be set"):
        InvalidRuntimeBuilder()


def test_entity_builder_accepts_complete_runtime_configuration() -> None:
    builder = ValidRuntimeBuilder()

    assert builder.get_executable_kind() == "function-valid"
    assert builder.get_action_from_task_kind("task-valid") == "valid"
    assert builder.get_task_kind_from_action("valid") == "task-valid"
    assert builder.get_run_kind_from_action("valid") == "run-valid"


def test_function_generic_builder_builds_entity_without_runtime_configuration() -> None:
    function = FunctionGenericBuilder().build(
        project="my-project",
        name="handler",
        kind="python",
        uuid="function-id",
        code_src="function.py",
        handler="handler",
    )

    assert function.project == "my-project"
    assert function.name == "handler"
    assert function.id == "function-id"
    assert function.kind == "python"
    assert function.spec.code_src == "function.py"
    assert function.spec.handler == "handler"
