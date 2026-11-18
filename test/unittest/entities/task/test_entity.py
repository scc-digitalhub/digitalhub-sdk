# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities.task._base.entity as task_entity
from digitalhub.entities.task._base.entity import Task


def test_task_run_operations_delegate_to_run_processor(monkeypatch) -> None:
    task = object.__new__(Task)
    run = Mock()
    build_task_run = Mock(return_value=run)
    create_run = Mock(return_value=run)
    get_run = Mock(return_value=run)
    delete_run = Mock(return_value={"deleted": True})
    monkeypatch.setattr(task_entity.run_processor, "build_task_run", build_task_run)
    monkeypatch.setattr(task_entity.run_processor, "create_run", create_run)
    monkeypatch.setattr(task_entity.run_processor, "get_run", get_run)
    monkeypatch.setattr(task_entity.run_processor, "delete_run", delete_run)

    assert task.run("python+run", save=False, labels=["run"]) is run
    build_task_run.assert_called_once_with(task, "python+run", save=False, labels=["run"])

    assert task.new_run(save=False, project="project") is run
    create_run.assert_called_once_with(save=False, project="project")

    assert task.get_run("run-key") is run
    get_run.assert_called_once_with("run-key")

    assert task.delete_run("run-key") == {"deleted": True}
    delete_run.assert_called_once_with("run-key")
