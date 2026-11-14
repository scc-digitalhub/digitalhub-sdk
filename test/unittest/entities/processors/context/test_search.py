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


def _entity(*, include_spec: bool = True) -> dict:
    entity = {
        "key": "store://demo/artifact/file/artifact-1:version-1",
        "kind": "file",
        "id": "version-1",
        "name": "artifact-1",
        "project": "demo",
        "metadata": {},
        "status": {},
    }
    if include_spec:
        entity["spec"] = {}
    return entity


def _processor(monkeypatch, entity: dict) -> tuple[ContextEntitySearchProcessor, Mock, Mock]:
    context = SimpleNamespace(name="demo", client=Mock())
    context.client.execute_list.return_value = [entity]
    monkeypatch.setattr(search_module, "get_context", Mock(return_value=context))
    crud_processor = Mock()
    return ContextEntitySearchProcessor(crud_processor), context.client, crud_processor


def test_search_builds_complete_entities_from_paginated_results(monkeypatch) -> None:
    entity = _entity()
    processor, client, crud_processor = _processor(monkeypatch, entity)

    result = processor.search_entity("demo", query="artifact")

    assert len(result[0]) == 1
    assert result[0][0].ENTITY_TYPE == "artifact"
    assert result[0][0].name == "artifact-1"
    assert result[1] == []
    client.execute_list.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.SEARCH,
            target=ContextProjectTarget("demo"),
            options=SearchOptions(query="artifact"),
        )
    )
    client.execute.assert_not_called()
    crud_processor.read_context_entity.assert_not_called()


def test_search_reads_summary_entities_to_hydrate_them(monkeypatch) -> None:
    entity = _entity(include_spec=False)
    processor, _, crud_processor = _processor(monkeypatch, entity)
    hydrated_entity = object()
    crud_processor.read_context_entity.return_value = hydrated_entity

    result = processor.search_entity("demo")

    assert result == ([hydrated_entity], [])
    crud_processor.read_context_entity.assert_called_once_with(
        entity["key"],
        entity_type="artifact",
    )


def test_search_keeps_unreadable_results_as_dead_entities(monkeypatch) -> None:
    entity = _entity(include_spec=False)
    processor, _, crud_processor = _processor(monkeypatch, entity)
    crud_processor.read_context_entity.side_effect = BackendError("not found")

    result = processor.search_entity("demo")

    assert result == ([], [entity])
