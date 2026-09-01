from unittest.mock import Mock

import digitalhub.entities._base.context.entity as context_entity_module
from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._base.metadata.entity import Metadata
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus


class StubContextEntity(ContextEntity):
    ENTITY_TYPE = "stub"


def _build_entity(name: str = "entity") -> StubContextEntity:
    entity = StubContextEntity(
        project="project",
        kind="stub-kind",
        metadata=Metadata(name=name, version="1"),
        spec=GenericSpec(value="spec"),
        status=GenericStatus(state="READY"),
        user="user",
    )
    entity.id = "entity-id"
    entity.key = f"store://project/stub/stub-kind/{name}:entity-id"
    return entity


def test_save_creates_entity_and_updates_attributes(monkeypatch) -> None:
    entity = _build_entity()
    saved = _build_entity("saved")
    create_entity = Mock(return_value=saved)
    monkeypatch.setattr(context_entity_module.crud_processor, "create_context_entity", create_entity)

    result = entity.save()

    assert result is entity
    create_entity.assert_called_once_with(_entity=entity)
    assert entity.metadata is saved.metadata
    assert entity.spec is saved.spec
    assert entity.status is saved.status
    assert entity.user == saved.user


def test_save_update_calls_update_processor(monkeypatch) -> None:
    entity = _build_entity()
    updated = _build_entity("updated")
    update_entity = Mock(return_value=updated)
    monkeypatch.setattr(context_entity_module.crud_processor, "update_context_entity", update_entity)
    entity_dict = entity.to_dict()

    result = entity.save(update=True)

    assert result is entity
    update_entity.assert_called_once_with(
        "project",
        "stub",
        "entity-id",
        entity_dict,
    )
    assert entity.metadata is updated.metadata


def test_export_delegates_to_processor(monkeypatch) -> None:
    entity = _build_entity()
    export_entity = Mock(return_value="entity.yaml")
    monkeypatch.setattr(context_entity_module.crud_processor, "export_context_entity", export_entity)

    assert entity.export() == "entity.yaml"
    export_entity.assert_called_once_with(entity)


def test_refresh_reads_key_and_updates_attributes(monkeypatch) -> None:
    entity = _build_entity()
    refreshed = _build_entity("refreshed")
    read_entity = Mock(return_value=refreshed)
    monkeypatch.setattr(context_entity_module.crud_processor, "read_context_entity", read_entity)

    result = entity.refresh()

    assert result is entity
    read_entity.assert_called_once_with(entity.key)
    assert entity.metadata is refreshed.metadata


def test_context_resolves_project_context(monkeypatch) -> None:
    entity = _build_entity()
    get_context = Mock(return_value="context")
    monkeypatch.setattr(context_entity_module, "get_context", get_context)

    assert entity._context() == "context"
    get_context.assert_called_once_with("project")
