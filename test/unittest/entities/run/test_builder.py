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
    ValidRuntimeBuilder()


def test_run_generic_builder_does_not_require_runtime_configuration() -> None:
    RunGenericBuilder()
