# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.search as search_module
from digitalhub.entities._processors.context.search import ContextEntitySearchProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import SearchOptions
from digitalhub.stores.client.compiler.targets import ContextProjectTarget
from digitalhub.utils.exceptions import BackendError


def test_search_entity_builds_query_and_separates_dead_records(monkeypatch) -> None:
    client = Mock()
    client.execute.return_value = {
        "content": [
            {"key": "store://context-project/function/function/function:live-id"},
            {"key": "store://context-project/function/function/function:dead-id", "kind": "function"},
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

    assert result == (
        ["live-entity"],
        [{"key": "store://context-project/function/function/function:dead-id", "kind": "function"}],
    )
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.SEARCH,
            target=ContextProjectTarget("context-project"),
            options=SearchOptions(query="pipeline", state="READY"),
        )
    )
    read_entity.assert_any_call("store://context-project/function/function/function:live-id", entity_type="function")
    read_entity.assert_any_call("store://context-project/function/function/function:dead-id", entity_type="function")
