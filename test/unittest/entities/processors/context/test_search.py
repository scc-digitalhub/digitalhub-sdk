from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.search as search_module
from digitalhub.entities._processors.context.search import ContextEntitySearchProcessor
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
from digitalhub.utils.exceptions import BackendError


def test_search_entity_builds_query_and_separates_dead_records(monkeypatch) -> None:
    client = Mock()
    api = object()
    client.build_parameters.return_value = {"query": "pipeline", "state": "READY"}
    client.build_api.return_value = api
    client.read_object.return_value = {
        "content": [
            {"key": "live-key"},
            {"key": "dead-key", "kind": "function"},
        ]
    }
    context = SimpleNamespace(name="context-project", client=client)
    read_entity = Mock(side_effect=["live-entity", BackendError("missing")])
    crud_processor = SimpleNamespace(read_context_entity=read_entity)
    monkeypatch.setattr(search_module, "get_context", Mock(return_value=context))

    result = ContextEntitySearchProcessor().search_entity(
        crud_processor,
        "project",
        query="pipeline",
        state="READY",
    )

    assert result == (["live-entity"], [{"key": "dead-key", "kind": "function"}])
    client.build_parameters.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.SEARCH.value,
        query="pipeline",
        entity_types=None,
        name=None,
        kind=None,
        created=None,
        updated=None,
        description=None,
        labels=None,
        state="READY",
    )
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.SEARCH.value,
        project="context-project",
    )
    client.read_object.assert_called_once_with(api, query="pipeline", state="READY")
    read_entity.assert_any_call("live-key")
    read_entity.assert_any_call("dead-key")
