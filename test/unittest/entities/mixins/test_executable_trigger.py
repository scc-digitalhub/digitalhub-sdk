from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.executable.trigger as trigger_module
from digitalhub.entities._mixin.executable.trigger import ExecutableTriggerMixin
from digitalhub.utils.exceptions import EntityError


class StubExecutable(ExecutableTriggerMixin):
    ENTITY_TYPE = "function"
    project = "project"
    kind = "python"
    name = "function"
    id = "function-id"
    key = "function-key"


def _trigger(executable: StubExecutable, trigger_id: str, trigger_key: str, function: str):
    return SimpleNamespace(
        id=trigger_id,
        key=trigger_key,
        spec=SimpleNamespace(function=function),
    )


def test_trigger_builds_template_and_saves_entity(monkeypatch) -> None:
    executable = StubExecutable()
    task = Mock()
    task._get_task_string.return_value = "task://project/task-id"
    executable._get_or_create_task = Mock(return_value=task)
    get_run_kind = Mock(return_value="python+run")
    get_spec_validator = Mock()
    validator = Mock()
    validator.return_value.to_dict.return_value = {"validated": True}
    get_spec_validator.return_value = validator
    build_entity = Mock(return_value=Mock())
    monkeypatch.setattr(trigger_module.entity_factory, "get_run_kind_from_action", get_run_kind)
    monkeypatch.setattr(trigger_module.entity_factory, "get_spec_validator", get_spec_validator)
    monkeypatch.setattr(trigger_module.entity_factory, "build_entity_from_params", build_entity)

    result = executable.trigger(
        action="execute",
        kind="lifecycle",
        name="on-demand",
        template={"custom": "value"},
        description="A trigger",
    )

    assert result is build_entity.return_value
    executable._get_or_create_task.assert_called_once_with("execute")
    get_run_kind.assert_called_once_with("python", "execute")
    get_spec_validator.assert_called_once_with("python+run")
    validator.assert_called_once_with(
        custom="value",
        task="task://project/task-id",
        function="python://project/function:function-id",
    )
    build_entity.assert_called_once_with(
        description="A trigger",
        project="project",
        kind="lifecycle",
        name="on-demand",
        function="python://project/function:function-id",
        task="task://project/task-id",
        template={"validated": True},
    )
    build_entity.return_value.save.assert_called_once_with()


def test_trigger_rejects_non_dictionary_template(monkeypatch) -> None:
    executable = StubExecutable()
    task = Mock()
    task._get_task_string.return_value = "task://project/task-id"
    executable._get_or_create_task = Mock(return_value=task)
    monkeypatch.setattr(trigger_module.entity_factory, "get_run_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(trigger_module.entity_factory, "get_spec_validator", Mock())

    with pytest.raises(EntityError, match="Template must be a dictionary"):
        executable.trigger("execute", "lifecycle", "on-demand", template="invalid")


def test_get_trigger_matches_id_or_key_and_rejects_other_executables() -> None:
    executable = StubExecutable()
    executable._list_triggers = Mock(
        return_value=[
            _trigger(executable, "trigger-id", "trigger-key", executable._get_executable_string()),
            _trigger(executable, "other-id", "other-key", "python://project/other:other-id"),
        ]
    )

    matching_trigger = executable._list_triggers.return_value[0]
    assert executable.get_trigger("trigger-id") is matching_trigger
    assert executable.get_trigger("trigger-key") is matching_trigger

    with pytest.raises(EntityError, match="Trigger 'other-id' does not exist"):
        executable.get_trigger("other-id")


def test_list_triggers_forwards_filters() -> None:
    executable = StubExecutable()
    executable._list_triggers = Mock(return_value=[])

    assert executable.list_triggers(q="query", task="task-key") == []
    executable._list_triggers.assert_called_once_with(
        q="query",
        name=None,
        kind=None,
        user=None,
        created=None,
        updated=None,
        versions=None,
        task="task-key",
    )


def test_list_triggers_filters_by_executable(monkeypatch) -> None:
    executable = StubExecutable()
    list_triggers = Mock(return_value=["trigger"])
    monkeypatch.setattr(trigger_module, "list_triggers", list_triggers)

    assert executable._list_triggers(state="READY") == ["trigger"]

    list_triggers.assert_called_once_with(
        "project",
        state="READY",
        function="python://project/function:function-id",
    )
