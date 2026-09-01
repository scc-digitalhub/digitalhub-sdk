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
    ValidRuntimeBuilder()


def test_workflow_generic_builder_does_not_require_runtime_configuration() -> None:
    WorkflowGenericBuilder()
