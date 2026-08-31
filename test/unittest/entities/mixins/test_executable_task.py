from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._mixin.executable.task as task_module
from digitalhub.entities._mixin.executable.task import ExecutableTaskMixin


def _executable(existing_task: Mock) -> ExecutableTaskMixin:
    executable = ExecutableTaskMixin()
    executable.ENTITY_TYPE = "function"
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
    replacement.save.assert_called_once_with(update=True)


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
    replacement.save.assert_called_once_with(update=True)
