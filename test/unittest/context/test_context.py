from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.context.context import Context
from digitalhub.entities._commons.enums import Relationship
from digitalhub.utils.exceptions import ContextError


def test_register_entity_requires_an_active_run() -> None:
    context = object.__new__(Context)
    context.run = None
    context.logged = {}
    entity = Mock()

    with pytest.raises(ContextError, match="active run"):
        context.register_entity(entity)

    entity.add_relationship.assert_not_called()
    assert context.logged == {}


def test_register_entity_records_producer_relationship() -> None:
    context = object.__new__(Context)
    context.run = SimpleNamespace(key="run-key", id="run-id")
    context.logged = {}
    entity = Mock(name="artifact")
    entity.name = "artifact"
    entity.key = "artifact-key"

    assert context.register_entity(entity) is entity

    entity.add_relationship.assert_called_once_with(Relationship.PRODUCEDBY.value, "run-key:run-id")
    assert context.logged == {"artifact": "artifact-key"}
