import importlib
from unittest.mock import Mock

from digitalhub.entities._mixin.executable.mixin import ExecutableMixin


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


def test_raise_if_exists_checks_resolved_task_kind(monkeypatch) -> None:
    executable = StubExecutable()
    executable._check_task_in_backend = Mock(return_value=False)
    method_module = importlib.import_module(executable._raise_if_exists.__module__)
    monkeypatch.setattr(method_module.entity_factory, "get_task_kind_from_action", Mock(return_value="task-kind"))

    executable._raise_if_exists("build")

    executable._check_task_in_backend.assert_called_once_with("task-kind")


def test_raise_if_not_exists_checks_resolved_task_kind(monkeypatch) -> None:
    executable = StubExecutable()
    executable._check_task_in_backend = Mock(return_value=True)
    method_module = importlib.import_module(executable._raise_if_not_exists.__module__)
    monkeypatch.setattr(method_module.entity_factory, "get_task_kind_from_action", Mock(return_value="task-kind"))

    executable._raise_if_not_exists("build")

    executable._check_task_in_backend.assert_called_once_with("task-kind")
