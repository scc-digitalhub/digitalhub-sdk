# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

from digitalhub.entities._mixin.executable.task import ExecutableTaskMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor


@pytest.fixture
def executable() -> ExecutableTaskMixin:
    return ExecutableTaskMixin()


@pytest.mark.parametrize(
    ("method", "processor_method"),
    [
        ("new_task", "create_task"),
        ("get_task", "get_task"),
        ("update_task", "update_task"),
        ("delete_task", "delete_task"),
        ("set_task", "set_task"),
    ],
)
def test_task_methods_delegate_to_executable_processor(executable, monkeypatch, method, processor_method) -> None:
    operation = Mock(return_value="result")
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        processor_method,
        operation,
    )

    if method == "delete_task":
        assert executable.delete_task("run", cascade=False) == "result"
        operation.assert_called_once_with(executable, "run", cascade=False)
    elif method == "get_task":
        assert executable.get_task("run") == "result"
        operation.assert_called_once_with(executable, "run")
    else:
        assert getattr(executable, method)("run", name="task") == "result"
        operation.assert_called_once_with(executable, "run", name="task")


def test_list_task_delegates_filters(monkeypatch) -> None:
    executable = ExecutableTaskMixin()
    list_tasks = Mock(return_value=[])
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        "list_tasks",
        list_tasks,
    )

    assert executable.list_tasks(q="query", state="RUNNING") == []
    list_tasks.assert_called_once_with(
        executable,
        q="query",
        name=None,
        kind=None,
        user=None,
        state="RUNNING",
        created=None,
        updated=None,
    )


def test_import_tasks_delegates_to_processor(monkeypatch) -> None:
    executable = ExecutableTaskMixin()
    import_tasks = Mock()
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        "import_tasks",
        import_tasks,
    )
    tasks = [{"kind": "task-kind"}]

    executable.import_tasks(tasks)

    import_tasks.assert_called_once_with(executable, tasks)
