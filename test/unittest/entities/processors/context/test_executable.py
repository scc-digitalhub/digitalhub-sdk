from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._processors.context.executable as executable_module
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
    imported.import_tasks = Mock()
    build_entity = Mock(side_effect=[executable, imported])
    create_entity = Mock(return_value={"kind": "function", "id": "new-id"})
    monkeypatch.setattr(executable_module, "read_yaml", Mock(return_value=[{"project": "project"}, {"kind": "task"}]))
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))
    crud_processor._create_context_entity = create_entity

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True)

    assert result is imported
    assert executable.id == "new-id"
    assert executable.metadata.version == "new-id"
    create_entity.assert_called_once_with(_context(), "function", executable.to_dict.return_value)
    imported.import_tasks.assert_called_once_with([{"kind": "task", "status": {}}])


def test_import_executable_converts_duplicate_error(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    monkeypatch.setattr(executable_module, "read_yaml", Mock(return_value={"project": "project"}))
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))
    crud_processor._create_context_entity.side_effect = EntityAlreadyExistsError("exists")

    with pytest.raises(EntityError, match="already exists"):
        processor.import_executable_entity(file="entity.yaml")


def test_load_executable_updates_existing_entity_and_imports_tasks(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.import_tasks = Mock()
    monkeypatch.setattr(executable_module, "read_yaml", Mock(return_value=[{"project": "project"}, {"kind": "task"}]))
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    result = processor.load_executable_entity("entity.yaml")

    assert result is executable
    crud_processor._update_context_entity.assert_called_once_with(
        _context(),
        "function",
        executable.id,
        executable.to_dict.return_value,
    )
    crud_processor._create_context_entity.assert_not_called()
    executable.import_tasks.assert_called_once_with([{"kind": "task"}])


def test_load_executable_creates_missing_entity(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor._update_context_entity.side_effect = EntityNotExistsError("missing")
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.import_tasks = Mock()
    monkeypatch.setattr(executable_module, "read_yaml", Mock(return_value={"project": "project"}))
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    result = processor.load_executable_entity("entity.yaml")

    assert result is executable
    crud_processor._create_context_entity.assert_called_once_with(
        _context(),
        "function",
        executable.to_dict.return_value,
    )
    executable.import_tasks.assert_called_once_with([])
