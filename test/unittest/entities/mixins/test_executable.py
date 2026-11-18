# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

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


def test_list_task_delegates_without_forwarding_project_twice(monkeypatch) -> None:
    executable = StubExecutable()
    list_tasks = Mock(return_value=[])
    monkeypatch.setattr(
        "digitalhub.entities._mixin.executable.task.executable_processor.list_tasks",
        list_tasks,
    )

    result = executable.list_task(q="query")

    assert result == []
    list_tasks.assert_called_once_with(
        executable,
        q="query",
        name=None,
        kind=None,
        user=None,
        state=None,
        created=None,
        updated=None,
    )
