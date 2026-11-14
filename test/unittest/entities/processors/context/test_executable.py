# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.context.executable as executable_module
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
    imported.import_tasks = Mock()
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
    imported.import_tasks.assert_called_once_with([{"kind": "task", "status": {}}])


def test_import_executable_updates_project_and_identity(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = VersionedExecutable()
    imported = VersionedExecutable(project="target-project", entity_id="new-id")
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
    imported.import_tasks.assert_called_once_with([{"kind": "task", "status": {}}])


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
    imported.import_tasks = Mock()
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
    imported.import_tasks.assert_called_once_with([{"kind": "task"}])


def test_load_executable_creates_missing_entity(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor._update_context_entity.side_effect = EntityNotExistsError("missing")
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    imported.import_tasks = Mock()
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
    imported.import_tasks.assert_called_once_with([])
