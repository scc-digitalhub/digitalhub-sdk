from typing import ClassVar

import pytest

from digitalhub.entities._commons.utils import KindAction
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.entities.workflow.generic.builder import WorkflowGenericBuilder
from digitalhub.utils.exceptions import EntityError


class InvalidRuntimeBuilder(WorkflowBuilder):
    ENTITY_CLASS = WorkflowGenericBuilder.ENTITY_CLASS
    ENTITY_SPEC_CLASS = WorkflowGenericBuilder.ENTITY_SPEC_CLASS
    ENTITY_SPEC_VALIDATOR = WorkflowGenericBuilder.ENTITY_SPEC_VALIDATOR
    ENTITY_STATUS_CLASS = WorkflowGenericBuilder.ENTITY_STATUS_CLASS
    ENTITY_KIND = "invalid-runtime"


class ValidRuntimeBuilder(InvalidRuntimeBuilder):
    EXECUTABLE_KIND = "workflow-valid"
    TASKS_KINDS: ClassVar[list[KindAction]] = [KindAction("task-valid", "valid")]
    RUN_KINDS: ClassVar[list[KindAction]] = [KindAction("run-valid", "valid")]


def test_workflow_builder_rejects_incomplete_runtime_configuration() -> None:
    with pytest.raises(EntityError, match="EXECUTABLE_KIND must be set"):
        InvalidRuntimeBuilder()


def test_workflow_builder_accepts_complete_runtime_configuration() -> None:
    builder = ValidRuntimeBuilder()

    assert builder.get_executable_kind() == "workflow-valid"
    assert builder.get_action_from_task_kind("task-valid") == "valid"
    assert builder.get_task_kind_from_action("valid") == "task-valid"
    assert builder.get_run_kind_from_action("valid") == "run-valid"


def test_workflow_generic_builder_builds_entity_without_runtime_configuration() -> None:
    workflow = WorkflowGenericBuilder().build(
        project="my-project",
        name="workflow",
        kind="python-workflow",
        uuid="workflow-id",
        code_src="workflow.py",
    )

    assert workflow.project == "my-project"
    assert workflow.name == "workflow"
    assert workflow.id == "workflow-id"
    assert workflow.kind == "python-workflow"
    assert workflow.spec.code_src == "workflow.py"
