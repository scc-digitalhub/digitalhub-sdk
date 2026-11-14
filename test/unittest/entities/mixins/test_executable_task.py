# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.executable.task as task_module
from digitalhub.entities._mixin.executable.task import ExecutableTaskMixin


def _executable(existing_task: Mock, entity_type: str = "function") -> ExecutableTaskMixin:
    executable = ExecutableTaskMixin()
    executable.ENTITY_TYPE = entity_type
    executable.project = "project"
    executable.kind = "python"
    executable.name = "function"
    executable.id = "function-id"
    executable._get_task_from_backend = Mock(return_value=[existing_task])
    return executable


def test_update_task_loads_existing_task_when_cache_is_cold(monkeypatch) -> None:
    existing_task = Mock(id="task-id")
    replacement = Mock()
    executable = _executable(existing_task)
    build_entity = Mock(return_value=replacement)
    monkeypatch.setattr(task_module.entity_factory, "get_task_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(task_module.entity_factory, "build_entity_from_params", build_entity)

    result = executable.update_task("run", name="updated")

    assert result is replacement
    build_entity.assert_called_once_with(
        name="updated",
        project="project",
        kind="python+run",
        function="python://project/function:function-id",
        uuid="task-id",
    )
    replacement.update.assert_called_once_with()


def test_delete_task_loads_existing_task_when_cache_is_cold(monkeypatch) -> None:
    existing_task = Mock(key="store://task/project/task-id")
    executable = _executable(existing_task)
    delete = Mock(return_value={"deleted": True})
    monkeypatch.setattr(task_module.entity_factory, "get_task_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(task_module, "delete_task", delete)

    result = executable.delete_task("run")

    assert result == {"deleted": True}
    delete.assert_called_once_with("store://task/project/task-id", cascade=True)
    assert executable._task_store() == {}


def test_set_task_preserves_existing_task_id_when_cache_is_cold(monkeypatch) -> None:
    existing_task = SimpleNamespace(id="task-id")
    replacement = Mock()
    executable = _executable(existing_task)
    build_entity = Mock(return_value=replacement)
    monkeypatch.setattr(task_module.entity_factory, "get_task_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(task_module.entity_factory, "build_entity_from_params", build_entity)

    result = executable.set_task("run", name="replacement")

    assert result is replacement
    build_entity.assert_called_once_with(
        name="replacement",
        project="project",
        function="python://project/function:function-id",
        kind="python+run",
        uuid="task-id",
    )
    replacement.update.assert_called_once_with()


@pytest.mark.parametrize("entity_type", ["function", "workflow"])
def test_import_tasks_matches_the_executable_entity_type(monkeypatch, entity_type: str) -> None:
    executable = _executable(Mock(), entity_type)
    task = SimpleNamespace(
        spec=SimpleNamespace(**{entity_type: executable._get_executable_string()}),
        kind="task-kind",
        save=Mock(),
    )
    build_entity = Mock(return_value=task)
    get_action = Mock(return_value="execute")
    monkeypatch.setattr(task_module.entity_factory, "build_entity_from_dict", build_entity)
    monkeypatch.setattr(task_module.entity_factory, "get_action_from_task_kind", get_action)

    executable.import_tasks([{"kind": "task-kind"}])

    assert executable._task_store()["execute"] is task
    build_entity.assert_called_once_with({"kind": "task-kind"}, entity_type="task")
    task.save.assert_called_once_with()
    get_action.assert_called_once_with(executable.kind, "task-kind")


def test_import_tasks_skips_specs_without_the_executable_reference(monkeypatch) -> None:
    executable = _executable(Mock(), "workflow")
    task = SimpleNamespace(spec=SimpleNamespace(), kind="task-kind", save=Mock())
    monkeypatch.setattr(task_module.entity_factory, "build_entity_from_dict", Mock(return_value=task))

    executable.import_tasks([{"kind": "task-kind"}])

    assert executable._task_store() == {}
