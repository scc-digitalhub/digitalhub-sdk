# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.context.executable as executable_module
from digitalhub.entities._commons.enums import Relationship
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError


def _context(name: str = "project") -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _executable() -> Mock:
    executable = Mock()
    executable.ENTITY_TYPE = "function"
    executable.name = "function"
    executable.project = "project"
    executable.to_dict.return_value = {"kind": "function"}
    return executable


def test_task_operations_use_backend_without_entity_cache(monkeypatch) -> None:
    crud_processor = Mock()
    existing_task = SimpleNamespace(id="task-id", key="task-key")
    crud_processor.list_context_entities.return_value = [existing_task]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )

    assert processor.get_task(executable, "run") is existing_task
    assert "_tasks" not in executable.__dict__

    crud_processor.list_context_entities.assert_called_once_with(
        project="project",
        entity_type="task",
        function="function-ref",
        kind="python+run",
    )


def test_get_task_reads_fresh_backend_state_on_every_call(monkeypatch) -> None:
    crud_processor = Mock()
    first = SimpleNamespace(id="task-1", key="task-key-1")
    second = SimpleNamespace(id="task-2", key="task-key-2")
    crud_processor.list_context_entities.side_effect = [[first], [second]]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )

    assert processor.get_task(executable, "run") is first
    assert processor.get_task(executable, "run") is second
    assert crud_processor.list_context_entities.call_count == 2


def test_create_task_rechecks_backend_and_handles_duplicate(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor.list_context_entities.side_effect = [[], []]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    task = Mock()
    task.save.side_effect = EntityAlreadyExistsError("exists")
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", Mock(return_value=task))

    with pytest.raises(EntityError, match="already exists"):
        processor.create_task(executable, "run")


def test_import_tasks_does_not_store_tasks_on_executable(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    task = SimpleNamespace(
        spec=SimpleNamespace(function="function-ref"),
        kind="python+run",
        save=Mock(),
    )
    monkeypatch.setattr(
        executable_module.entity_factory,
        "build_entity_from_dict",
        Mock(return_value=task),
    )

    processor.import_tasks(executable, [{"kind": "python+run"}])

    task.save.assert_called_once_with()
    assert "_tasks" not in executable.__dict__


def test_list_executable_runs_applies_relationship_filter() -> None:
    crud_processor = Mock()
    crud_processor.list_context_entities.return_value = ["run"]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable._get_executable_string.return_value = "function-key"

    result = processor.list_executable_runs(executable, state="RUNNING")

    assert result == ["run"]
    crud_processor.list_context_entities.assert_called_once_with(
        project="project",
        entity_type="run",
        state="RUNNING",
        function="function-key",
    )


def test_get_executable_run_matches_id_or_key() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    first = SimpleNamespace(id="run-id", key="run-key")
    processor.list_executable_runs = Mock(return_value=[first])

    assert processor.get_executable_run(executable, "run-id") is first
    assert processor.get_executable_run(executable, "run-key") is first

    with pytest.raises(EntityError, match="does not belong"):
        processor.get_executable_run(executable, "missing")


def test_create_run_applies_relationship_and_extensions(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    executable.key = "function-key"
    executable.kind = "python"
    task = Mock()
    run = Mock()
    run.extensions = [{"name": "task-extension"}]
    task.run.return_value = run
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_run_kind_from_action",
        Mock(return_value="python+run"),
    )

    result = processor.create_run(
        executable,
        task,
        "execute",
        extensions=[{"name": "run-extension"}],
        parameter="value",
    )

    assert result is run
    task.run.assert_called_once_with("python+run", save=False, parameter="value")
    assert run.extensions == [{"name": "task-extension"}, {"name": "run-extension"}]
    run.add_relationship.assert_called_once_with(Relationship.RUN_OF.value, "function-key")
    run.save.assert_called_once_with()


def test_list_and_get_executable_trigger() -> None:
    crud_processor = Mock()
    trigger = SimpleNamespace(id="trigger-id", key="trigger-key")
    crud_processor.list_context_entities.return_value = [trigger]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable._get_executable_string.return_value = "function-ref"

    assert processor.list_executable_triggers(executable, state="READY") == [trigger]
    assert processor.get_executable_trigger(executable, "trigger-key") is trigger
    crud_processor.list_context_entities.assert_any_call(
        project="project",
        entity_type="trigger",
        state="READY",
        function="function-ref",
    )


def test_create_trigger_builds_spec_without_mutating_template(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    task = Mock()
    task._get_task_string.return_value = "task-ref"
    processor.get_or_create_task = Mock(return_value=task)
    spec = Mock()
    spec.to_dict.return_value = {"validated": True}
    build_spec = Mock(return_value=spec)
    trigger = Mock()
    build_entity = Mock(return_value=trigger)
    monkeypatch.setattr(executable_module.entity_factory, "get_run_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(executable_module.entity_factory, "build_spec", build_spec)
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", build_entity)
    template = {"custom": "value"}

    result = processor.create_trigger(
        executable,
        "execute",
        "lifecycle",
        "on-demand",
        template=template,
        description="A trigger",
    )

    assert result is trigger
    assert template == {"custom": "value"}
    build_spec.assert_called_once_with(
        "python+run",
        custom="value",
        task="task-ref",
        function="function-ref",
    )
    build_entity.assert_called_once_with(
        description="A trigger",
        project="project",
        kind="lifecycle",
        name="on-demand",
        function="function-ref",
        task="task-ref",
        template={"validated": True},
    )
    trigger.save.assert_called_once_with()


class VersionedExecutable(VersionedMixin):
    ENTITY_TYPE = "function"

    def __init__(self, project: str = "project", entity_id: str = "entity-id") -> None:
        self.project = project
        self.kind = "function"
        self.metadata = SimpleNamespace(project=project, version=entity_id)
        self._init_versioned_identity(project, "function", entity_id, self.kind)
        self.import_tasks = Mock()

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "kind": self.kind,
            "name": self.name,
            "id": self.id,
            "key": self.key,
            "metadata": {
                "project": self.metadata.project,
                "version": self.metadata.version,
            },
        }


def test_import_executable_rejects_missing_or_ambiguous_source() -> None:
    processor = ContextEntityExecutableProcessor(Mock())

    with pytest.raises(ValueError, match="Provide key or file"):
        processor.import_executable_entity()

    with pytest.raises(ValueError, match="Provide key or file"):
        processor.import_executable_entity(file="entity.yaml", key="entity-key")


def test_import_executable_reads_file_resets_id_and_imports_tasks(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    processor.import_tasks = Mock()
    build_entity = Mock(side_effect=[executable, imported])
    create_entity = Mock(return_value={"kind": "function", "id": "new-id"})
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(
            return_value=[
                {"project": "project", "key": "store://project/function/function/function:entity-id"},
                {"kind": "task"},
            ]
        ),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))
    crud_processor._create_context_entity = create_entity

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True)

    assert result is imported
    assert executable.id == "new-id"
    assert executable.metadata.version == "new-id"
    create_entity.assert_called_once_with(_context(), "function", executable.to_dict.return_value)
    processor.import_tasks.assert_called_once_with(imported, [{"kind": "task", "status": {}}])


def test_import_executable_updates_project_and_identity(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = VersionedExecutable()
    imported = VersionedExecutable(project="target-project", entity_id="new-id")
    processor.import_tasks = Mock()
    context = _context("target-project")
    response = imported.to_dict()
    crud_processor._create_context_entity.return_value = response
    build_entity = Mock(side_effect=[executable, imported])
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(
            return_value=[
                {"project": "project", "key": "store://project/function/function/function:entity-id"},
                {"kind": "task"},
            ]
        ),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=context))
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True, context="target-project")

    assert result is imported
    assert executable.project == "target-project"
    assert executable.id == "new-id"
    assert executable.metadata.project == "target-project"
    assert executable.metadata.version == "new-id"
    assert executable.key == "store://target-project/function/function/function:new-id"
    crud_processor._create_context_entity.assert_called_once_with(context, "function", executable.to_dict())
    processor.import_tasks.assert_called_once_with(imported, [{"kind": "task", "status": {}}])


def test_import_executable_converts_duplicate_error(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))
    crud_processor._create_context_entity.side_effect = EntityAlreadyExistsError("exists")

    with pytest.raises(EntityError, match="already exists"):
        processor.import_executable_entity(file="entity.yaml")


def test_load_executable_updates_existing_entity_and_imports_tasks(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    processor.import_tasks = Mock()
    backend_response = {"project": "project", "kind": "function", "id": "backend-id"}
    crud_processor._update_context_entity.return_value = backend_response
    build_entity = Mock(side_effect=[executable, imported])
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(
            return_value=[
                {"project": "project", "key": "store://project/function/function/function:entity-id"},
                {"kind": "task"},
            ]
        ),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.load_executable_entity("entity.yaml")

    assert result is imported
    crud_processor._update_context_entity.assert_called_once_with(
        _context(),
        "function",
        executable.id,
        executable.to_dict.return_value,
    )
    crud_processor._create_context_entity.assert_not_called()
    assert build_entity.call_args_list[1] == call(backend_response, entity_type="function")
    processor.import_tasks.assert_called_once_with(imported, [{"kind": "task"}])


def test_load_executable_creates_missing_entity(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor._update_context_entity.side_effect = EntityNotExistsError("missing")
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    processor.import_tasks = Mock()
    backend_response = {"project": "project", "kind": "function", "id": "backend-id"}
    crud_processor._create_context_entity.return_value = backend_response
    build_entity = Mock(side_effect=[executable, imported])
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.load_executable_entity("entity.yaml")

    assert result is imported
    crud_processor._create_context_entity.assert_called_once_with(
        _context(),
        "function",
        executable.to_dict.return_value,
    )
    assert build_entity.call_args_list[1] == call(backend_response, entity_type="function")
    processor.import_tasks.assert_called_once_with(imported, [])
