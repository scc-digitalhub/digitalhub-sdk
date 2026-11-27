from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.context.crud as crud_module
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.utils import update_entity_identity
from digitalhub.entities.task._base.entity import Task
from digitalhub.stores.client.common.enums import BackendOp
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

    def _update_attributes(self, obj) -> None:
        self.stored = obj


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
    context = _fake_context("target-project")
    context.client.execute.return_value = saved_entity.to_dict()
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

    assert result is entity
    assert entity.stored is saved_entity
    assert entity.project == "target-project"
    assert entity.id == expected_id
    assert entity.metadata.project == "target-project"
    assert entity.metadata.version == expected_id
    assert entity.key == f"store://target-project/artifact/artifact-kind/artifact-name:{expected_id}"
    assert _operations(context) == [(BackendOp.CREATE, entity.to_dict())]


@pytest.mark.parametrize("missing", [False, True])
def test_load_context_entity_returns_backend_entity(monkeypatch, missing: bool) -> None:
    processor = ContextEntityCRUDProcessor()
    source_entity = VersionedEntity()
    backend_entity = VersionedEntity(project="project", entity_id="backend-id")
    backend_response = backend_entity.to_dict()
    context = _fake_context("source-project")

    def execute(op):
        if missing and op.operation == BackendOp.UPDATE:
            raise EntityNotExistsError("missing")
        return backend_response

    context.client.execute.side_effect = execute
    build_entity = Mock(side_effect=[source_entity, backend_entity])
    monkeypatch.setattr(crud_module, "read_yaml", Mock(return_value=_entity_dict()))
    monkeypatch.setattr(crud_module, "get_context", Mock(return_value=context))
    monkeypatch.setattr(crud_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.load_context_entity("entity.yaml")

    assert result is source_entity
    assert source_entity.stored is backend_entity
    assert build_entity.call_args_list[1] == call(backend_response, entity_type="artifact")
    expected = [BackendOp.UPDATE, BackendOp.CREATE] if missing else [BackendOp.UPDATE]
    assert [operation for operation, _ in _operations(context)] == expected


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


def _fake_context(name: str = "project") -> Mock:
    context = Mock()
    context.name = name
    return context


def _operations(context: Mock) -> list[tuple]:
    """Operations and payloads the processor sent through the context client."""
    return [(c.args[0].operation, c.args[0].payload) for c in context.client.execute.call_args_list]


def _stored_entity_double() -> SimpleNamespace:
    return SimpleNamespace(
        project="project",
        ENTITY_TYPE="artifact",
        id="entity-id",
        key="store://project/artifact/artifact/entity:entity-id",
        to_dict=Mock(return_value={"id": "local"}),
        _update_attributes=Mock(),
    )


def test_create_context_entity_posts_the_entity_and_updates_it_with_the_stored_one(monkeypatch) -> None:
    processor = ContextEntityCRUDProcessor()
    context = _fake_context()
    context.client.execute.return_value = {"id": "stored"}
    monkeypatch.setattr(crud_module, "get_context", Mock(return_value=context))
    build_from_dict = Mock(return_value="stored-entity")
    monkeypatch.setattr(crud_module.entity_factory, "build_entity_from_dict", build_from_dict)
    entity = _stored_entity_double()

    assert processor.create_context_entity(entity) is entity

    crud_module.get_context.assert_called_once_with("project")
    assert _operations(context) == [(BackendOp.CREATE, {"id": "local"})]
    build_from_dict.assert_called_once_with({"id": "stored"}, entity_type="artifact")
    entity._update_attributes.assert_called_once_with("stored-entity")


def test_update_context_entity_puts_the_entity_and_updates_it_with_the_stored_one(monkeypatch) -> None:
    processor = ContextEntityCRUDProcessor()
    context = _fake_context()
    context.client.execute.return_value = {"id": "stored"}
    monkeypatch.setattr(crud_module, "get_context", Mock(return_value=context))
    build_from_dict = Mock(return_value="stored-entity")
    monkeypatch.setattr(crud_module.entity_factory, "build_entity_from_dict", build_from_dict)
    entity = _stored_entity_double()

    assert processor.update_context_entity(entity) is entity

    crud_module.get_context.assert_called_once_with("project")
    assert _operations(context) == [(BackendOp.UPDATE, {"id": "local"})]
    build_from_dict.assert_called_once_with({"id": "stored"}, entity_type="artifact")
    entity._update_attributes.assert_called_once_with("stored-entity")


def test_refresh_context_entity_updates_the_entity_with_the_stored_one() -> None:
    processor = ContextEntityCRUDProcessor()
    processor.read_context_entity = Mock(return_value="stored-entity")
    entity = _stored_entity_double()

    assert processor.refresh_context_entity(entity) is entity

    processor.read_context_entity.assert_called_once_with(entity.key, entity_type="artifact")
    entity._update_attributes.assert_called_once_with("stored-entity")


def test_create_context_entity_from_params_builds_runs_the_hook_and_creates(monkeypatch) -> None:
    processor = ContextEntityCRUDProcessor()
    processor.create_context_entity = Mock(return_value="stored-entity")
    entity = Mock()
    build_from_params = Mock(return_value=entity)
    monkeypatch.setattr(crud_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="artifact"))
    monkeypatch.setattr(crud_module.entity_factory, "build_entity_from_params", build_from_params)

    result = processor.create_context_entity_from_params("artifact", project="project", kind="artifact", name="data")

    assert result == "stored-entity"
    build_from_params.assert_called_once_with(entity_type="artifact", project="project", kind="artifact", name="data")
    entity._post_create_hook_before_save.assert_called_once_with()
    processor.create_context_entity.assert_called_once_with(entity)


def test_create_context_entity_from_params_rejects_a_kind_of_another_type(monkeypatch) -> None:
    processor = ContextEntityCRUDProcessor()
    processor.create_context_entity = Mock()
    monkeypatch.setattr(crud_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="model"))

    with pytest.raises(ValueError, match="does not match expected type 'model'"):
        processor.create_context_entity_from_params("artifact", project="project", kind="model")

    processor.create_context_entity.assert_not_called()
