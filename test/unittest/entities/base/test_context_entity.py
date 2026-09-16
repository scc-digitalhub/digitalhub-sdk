# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

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


def test_export_delegates_to_processor(monkeypatch) -> None:
    entity = _build_entity()
    export_entity = Mock(return_value="entity.yaml")
    monkeypatch.setattr(context_entity_module.crud_processor, "export_context_entity", export_entity)

    assert entity.export() == "entity.yaml"
    export_entity.assert_called_once_with(entity)


def test_context_resolves_project_context(monkeypatch) -> None:
    entity = _build_entity()
    get_context = Mock(return_value="context")
    monkeypatch.setattr(context_entity_module, "get_context", get_context)

    assert entity._context() == "context"
    get_context.assert_called_once_with("project")
