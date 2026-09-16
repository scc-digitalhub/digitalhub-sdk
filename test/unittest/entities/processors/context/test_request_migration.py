# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities._processors.context.crud as context_crud_module
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import (
    DeleteAllVersionsOptions,
    ListOptions,
    NoOptions,
    ReadAllVersionsOptions,
    ReadOptions,
)
from digitalhub.stores.client.compiler.targets import ContextCollectionTarget, ContextEntityTarget


def test_create_context_entity_uses_backend_operation_request() -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute.return_value = {"id": "artifact-id"}
    entity = {"name": "artifact"}

    result = ContextEntityCRUDProcessor()._create_context_entity(context, "artifact", entity)

    assert result == {"id": "artifact-id"}
    context.client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.CREATE,
            target=ContextCollectionTarget("demo", "artifact"),
            options=NoOptions(),
            payload=entity,
        )
    )


def test_read_context_entity_by_name_uses_first_list_result(monkeypatch) -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute_first.return_value = {"name": "artifact"}
    monkeypatch.setattr(
        context_crud_module,
        "parse_identifier",
        lambda *args, **kwargs: ("demo", "artifact", None, "artifact", None),
    )

    result = ContextEntityCRUDProcessor()._read_context_entity(context, "artifact")

    assert result == {"name": "artifact"}
    context.client.execute_first.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.LIST,
            target=ContextCollectionTarget("demo", "artifact"),
            options=ListOptions(name="artifact"),
        )
    )


def test_read_context_entity_by_id_uses_read_operation(monkeypatch) -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute.return_value = {"id": "artifact-id"}
    monkeypatch.setattr(
        context_crud_module,
        "parse_identifier",
        lambda *args, **kwargs: ("demo", "artifact", None, None, "artifact-id"),
    )

    result = ContextEntityCRUDProcessor()._read_context_entity(context, "artifact-id")

    assert result == {"id": "artifact-id"}
    context.client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.READ,
            target=ContextEntityTarget("demo", "artifact", "artifact-id"),
            options=ReadOptions(),
        )
    )


def test_read_context_entity_versions_uses_list_operation(monkeypatch) -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute_list.return_value = [{"name": "artifact"}]
    monkeypatch.setattr(
        context_crud_module,
        "parse_identifier",
        lambda *args, **kwargs: ("demo", "artifact", None, "artifact", None),
    )

    result = ContextEntityCRUDProcessor()._read_context_entity_versions(context, "artifact")

    assert result == [{"name": "artifact"}]
    context.client.execute_list.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.READ_ALL_VERSIONS,
            target=ContextCollectionTarget("demo", "artifact"),
            options=ReadAllVersionsOptions(name="artifact"),
        )
    )


def test_list_context_entities_uses_paginated_execution() -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute_list.return_value = [{"name": "artifact"}]

    result = ContextEntityCRUDProcessor()._list_context_entities(context, "artifact", q="ready")

    assert result == [{"name": "artifact"}]
    context.client.execute_list.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.LIST,
            target=ContextCollectionTarget("demo", "artifact"),
            options=ListOptions(q="ready"),
        )
    )


def test_update_context_entity_uses_backend_operation_request() -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute.return_value = {"id": "artifact-id"}
    entity = {"status": {"state": "READY"}}

    result = ContextEntityCRUDProcessor()._update_context_entity(context, "artifact", "artifact-id", entity)

    assert result == {"id": "artifact-id"}
    context.client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.UPDATE,
            target=ContextEntityTarget("demo", "artifact", "artifact-id"),
            options=NoOptions(),
            payload=entity,
        )
    )


def test_delete_context_entity_all_versions_uses_semantic_parameters(monkeypatch) -> None:
    context = Mock(name="context")
    context.name = "demo"
    context.client.execute.return_value = {"deleted": True}
    monkeypatch.setattr(
        context_crud_module,
        "parse_identifier",
        lambda *args, **kwargs: ("demo", "artifact", None, "artifact", None),
    )

    result = ContextEntityCRUDProcessor()._delete_context_entity(
        context,
        "artifact",
        delete_all_versions=True,
        cascade=True,
    )

    assert result == {"deleted": True}
    context.client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.DELETE_ALL_VERSIONS,
            target=ContextCollectionTarget("demo", "artifact"),
            options=DeleteAllVersionsOptions(name="artifact", cascade=True),
        )
    )
