from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.executable.task as task_module
from digitalhub.entities._mixin.executable.mixin import ExecutableMixin
from digitalhub.utils.exceptions import EntityError


class StubExecutable(ExecutableMixin):
    ENTITY_TYPE = "function"
    project = "project"
    kind = "function-kind"
    name = "function-name"
    id = "function-id"
    key = "function-key"

    def run(self, *args, **kwargs):
        return None


def test_list_task_does_not_forward_project_twice() -> None:
    executable = StubExecutable()
    executable._list_tasks = Mock(return_value=[])

    result = executable.list_task(q="query")

    assert result == []
    assert executable._list_tasks.call_args.args == ()
    assert executable._list_tasks.call_args.kwargs["q"] == "query"


def test_new_task_builds_and_caches_task_when_action_is_missing(monkeypatch) -> None:
    executable = StubExecutable()
    task = Mock()
    list_tasks = Mock(return_value=[])
    build_entity = Mock(return_value=task)
    monkeypatch.setattr(task_module.crud_processor, "list_context_entities", list_tasks)
    monkeypatch.setattr(task_module.entity_factory, "get_task_kind_from_action", Mock(return_value="task-kind"))
    monkeypatch.setattr(task_module.entity_factory, "build_entity_from_params", build_entity)

    result = executable.new_task("build", name="task")

    assert result is task
    assert executable._task_store()["build"] is task
    task.save.assert_called_once_with()
    build_entity.assert_called_once_with(
        name="task",
        project="project",
        function="function-kind://project/function-name:function-id",
        kind="task-kind",
    )


def test_new_task_rejects_existing_action(monkeypatch) -> None:
    executable = StubExecutable()
    list_tasks = Mock(return_value=[Mock()])
    build_entity = Mock()
    monkeypatch.setattr(task_module.crud_processor, "list_context_entities", list_tasks)
    monkeypatch.setattr(task_module.entity_factory, "get_task_kind_from_action", Mock(return_value="task-kind"))
    monkeypatch.setattr(task_module.entity_factory, "build_entity_from_params", build_entity)

    with pytest.raises(EntityError, match="Task 'build' already exists"):
        executable.new_task("build")

    build_entity.assert_not_called()
