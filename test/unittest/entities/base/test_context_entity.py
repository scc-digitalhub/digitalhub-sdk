# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

import digitalhub.entities._base.context.entity as context_entity_module
from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._base.metadata.entity import Metadata
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor


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
    entity.name = name
    entity.key = f"store://project/stub/stub-kind/{name}:entity-id"
    return entity


@pytest.mark.parametrize(
    ("method", "processor_method"),
    [
        ("save", "create_context_entity"),
        ("update", "update_context_entity"),
        ("refresh", "refresh_context_entity"),
    ],
)
def test_persistence_goes_through_the_processor(method: str, processor_method: str, monkeypatch) -> None:
    # The processor updates the entity with the stored state and returns it.
    entity = _build_entity()
    processor = Mock(return_value=entity)
    monkeypatch.setattr(ContextEntityCRUDProcessor, processor_method, processor)

    assert getattr(entity, method)() is entity
    processor.assert_called_once_with(entity)


def test_export_delegates_to_processor(monkeypatch) -> None:
    entity = _build_entity()
    export_entity = Mock(return_value="entity.yaml")
    monkeypatch.setattr(ContextEntityCRUDProcessor, "export_context_entity", export_entity)

    assert entity.export() == "entity.yaml"
    export_entity.assert_called_once_with(entity)


def test_context_resolves_project_context(monkeypatch) -> None:
    entity = _build_entity()
    get_context = Mock(return_value="context")
    monkeypatch.setattr(context_entity_module, "get_context", get_context)

    assert entity._context() == "context"
    get_context.assert_called_once_with("project")
