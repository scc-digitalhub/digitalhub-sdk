from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.context.crud as crud_module
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.utils import update_entity_identity
from digitalhub.entities.task._base.entity import Task
from digitalhub.utils.exceptions import EntityNotExistsError


class VersionedEntity(VersionedMixin):
    ENTITY_TYPE = "artifact"

    def __init__(self, project: str = "source-project", entity_id: str = "old-id") -> None:
        self.project = project
        self.kind = "artifact-kind"
        self.metadata = SimpleNamespace(project=project, version=entity_id)
        self._init_versioned_identity(project, "artifact-name", entity_id, self.kind)

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


def _entity_dict() -> dict:
    return {
        "project": "source-project",
        "key": "store://source-project/artifact/artifact-kind/artifact-name:old-id",
    }


@pytest.mark.parametrize(
    ("reset_id", "expected_id"),
    [(False, "old-id"), (True, "new-id")],
)
def test_import_context_entity_updates_project_and_identity(monkeypatch, reset_id: bool, expected_id: str) -> None:
    processor = ContextEntityCRUDProcessor()
    entity = VersionedEntity()
    saved_entity = VersionedEntity(project="target-project", entity_id=expected_id)
    context = SimpleNamespace(name="target-project")
    response = saved_entity.to_dict()
    processor._create_context_entity = Mock(return_value=response)
    build_entity = Mock(side_effect=[entity, saved_entity])
    monkeypatch.setattr(crud_module, "read_yaml", Mock(return_value=_entity_dict()))
    monkeypatch.setattr(crud_module, "get_context", Mock(return_value=context))
    monkeypatch.setattr(crud_module, "build_uuid", Mock(return_value="new-id"))
    monkeypatch.setattr(crud_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.import_context_entity(
        file="entity.yaml",
        reset_id=reset_id,
        context="target-project",
    )

    assert result is saved_entity
    assert entity.project == "target-project"
    assert entity.id == expected_id
    assert entity.metadata.project == "target-project"
    assert entity.metadata.version == expected_id
    assert entity.key == f"store://target-project/artifact/artifact-kind/artifact-name:{expected_id}"
    processor._create_context_entity.assert_called_once_with(context, "artifact", entity.to_dict())


@pytest.mark.parametrize("missing", [False, True])
def test_load_context_entity_returns_backend_entity(monkeypatch, missing: bool) -> None:
    processor = ContextEntityCRUDProcessor()
    source_entity = VersionedEntity()
    backend_entity = VersionedEntity(project="project", entity_id="backend-id")
    backend_response = backend_entity.to_dict()
    context = SimpleNamespace(name="source-project")
    processor._update_context_entity = Mock(
        side_effect=EntityNotExistsError("missing") if missing else None,
        return_value=backend_response,
    )
    processor._create_context_entity = Mock(return_value=backend_response)
    build_entity = Mock(side_effect=[source_entity, backend_entity])
    monkeypatch.setattr(crud_module, "read_yaml", Mock(return_value=_entity_dict()))
    monkeypatch.setattr(crud_module, "get_context", Mock(return_value=context))
    monkeypatch.setattr(crud_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.load_context_entity("entity.yaml")

    assert result is backend_entity
    assert build_entity.call_args_list[1] == call(backend_response, entity_type="artifact")
    if missing:
        processor._create_context_entity.assert_called_once_with(context, "artifact", source_entity.to_dict())
    else:
        processor._create_context_entity.assert_not_called()


def test_update_entity_identity_rebuilds_unversioned_task_key() -> None:
    task = object.__new__(Task)
    task.project = "source-project"
    task.kind = "python+run"
    task.metadata = SimpleNamespace(project="source-project", version="old-id")
    task._init_unversioned_identity("source-project", "old-id", task.kind)

    update_entity_identity(task, "target-project", "new-id")

    assert task.project == "target-project"
    assert task.id == "new-id"
    assert task.name == "new-id"
    assert task.metadata.project == "target-project"
    assert task.metadata.version == "new-id"
    assert task.key == "store://target-project/task/python+run/new-id"
