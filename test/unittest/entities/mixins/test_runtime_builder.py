import pytest

from digitalhub.entities._commons.utils import KindAction
from digitalhub.entities._mixin.runtime_entity.builder import RuntimeEntityBuilder
from digitalhub.utils.exceptions import EntityError


@pytest.fixture
def runtime_builder() -> RuntimeEntityBuilder:
    builder = RuntimeEntityBuilder()
    builder.EXECUTABLE_KIND = "function"
    builder.TASKS_KINDS = [KindAction("task", "execute")]
    builder.RUN_KINDS = [KindAction("run", "execute")]
    return builder


def test_runtime_builder_resolves_kinds_and_actions(runtime_builder: RuntimeEntityBuilder) -> None:
    assert runtime_builder.get_action_from_task_kind("task") == "execute"
    assert runtime_builder.get_task_kind_from_action("execute") == "task"
    assert runtime_builder.get_run_kind_from_action("execute") == "run"
    assert runtime_builder.get_executable_kind() == "function"
    assert runtime_builder.get_all_kinds() == ["function", "run", "task"]
    assert runtime_builder.get_all_actions() == ["execute"]


@pytest.mark.parametrize(
    ("method_name", "value", "message"),
    [
        ("get_action_from_task_kind", "missing", "Task kind missing not allowed"),
        ("get_task_kind_from_action", "missing", "Action missing not allowed"),
        ("get_run_kind_from_action", "missing", "Action missing not allowed"),
    ],
)
def test_runtime_builder_rejects_unknown_mappings(
    runtime_builder: RuntimeEntityBuilder,
    method_name: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(EntityError, match=message):
        getattr(runtime_builder, method_name)(value)


@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    [
        ("TASKS_KINDS", "invalid", "must be a list"),
        ("TASKS_KINDS", ["invalid"], "must be a list of KindAction"),
        ("RUN_KINDS", [KindAction(None, "execute")], "with kind set"),
    ],
)
def test_runtime_builder_validates_mapping_configuration(
    runtime_builder: RuntimeEntityBuilder,
    attribute: str,
    value,
    message: str,
) -> None:
    setattr(runtime_builder, attribute, value)

    with pytest.raises(EntityError, match=message):
        runtime_builder._validate_runtime_attributes()
