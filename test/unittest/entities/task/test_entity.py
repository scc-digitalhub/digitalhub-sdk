# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from digitalhub.entities.task._base.entity import Task
from digitalhub.entities.task._base.processor import TaskProcessor


def test_task_run_delegates_to_executable_processor(monkeypatch) -> None:
    task = object.__new__(Task)
    run = Mock()
    build_task_run = Mock(return_value=run)
    monkeypatch.setattr(TaskProcessor, "build_run", build_task_run)

    assert task.run("python+run", save=False, labels=["run"]) is run
    build_task_run.assert_called_once_with(task, "python+run", save=False, labels=["run"])
    assert not hasattr(task, "new_run")
    assert not hasattr(task, "get_run")
    assert not hasattr(task, "delete_run")
