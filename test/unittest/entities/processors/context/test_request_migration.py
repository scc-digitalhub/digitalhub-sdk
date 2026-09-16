# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities._processors.context.crud as context_crud_module
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import ctx_entity_id_ra, ctx_entity_ra
from digitalhub.stores.client.compiler.operation import ClientOp


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
            operation=BEOps.CREATE,
            route_args=ctx_entity_ra("demo", "artifact"),
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
            operation=BEOps.LIST,
            route_args=ctx_entity_ra("demo", "artifact"),
            params={"name": "artifact"},
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
            operation=BEOps.READ,
            route_args=ctx_entity_id_ra("demo", "artifact", "artifact-id"),
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
            operation=BEOps.LIST,
            route_args=ctx_entity_ra("demo", "artifact"),
            params={"name": "artifact", "versions": "all"},
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
            operation=BEOps.LIST,
            route_args=ctx_entity_ra("demo", "artifact"),
            params={"q": "ready"},
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
            operation=BEOps.UPDATE,
            route_args=ctx_entity_id_ra("demo", "artifact", "artifact-id"),
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
            operation=BEOps.DELETE_ALL_VERSIONS,
            route_args=ctx_entity_ra("demo", "artifact"),
            params={"name": "artifact", "cascade": True},
        )
    )
