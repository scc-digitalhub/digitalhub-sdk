# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import base_entity_ra, base_ra
from digitalhub.stores.client.compiler.operation import ClientOp


def test_create_base_entity_uses_backend_operation_request() -> None:
    client = Mock()
    client.execute.return_value = {"id": "project-id"}
    entity = {"name": "demo"}

    result = BaseEntityCRUDProcessor()._create_base_entity(client, "project", entity)

    assert result == {"id": "project-id"}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BEOps.CREATE,
            route_args=base_ra("project"),
            payload=entity,
        )
    )


def test_read_base_entity_uses_only_ra() -> None:
    client = Mock()
    client.execute.return_value = {"name": "demo"}

    result = BaseEntityCRUDProcessor()._read_base_entity(client, "project", "demo")

    assert result == {"name": "demo"}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BEOps.READ,
            route_args=base_entity_ra("project", "demo"),
        )
    )


def test_list_base_entities_uses_paginated_execution() -> None:
    client = Mock()
    client.execute_list.return_value = [{"name": "demo"}]

    result = BaseEntityCRUDProcessor()._list_base_entities(
        client,
        "project",
    )

    assert result == [{"name": "demo"}]
    client.execute_list.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BEOps.LIST,
            route_args=base_ra("project"),
        )
    )


def test_update_base_entity_uses_backend_operation_request() -> None:
    client = Mock()
    client.execute.return_value = {"name": "updated"}
    entity = {"name": "updated"}

    result = BaseEntityCRUDProcessor()._update_base_entity(client, "project", "demo", entity)

    assert result == {"name": "updated"}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BEOps.UPDATE,
            route_args=base_entity_ra("project", "demo"),
            payload=entity,
        )
    )


def test_delete_base_entity_uses_semantic_parameters() -> None:
    client = Mock()
    client.execute.return_value = {"deleted": True}

    result = BaseEntityCRUDProcessor()._delete_base_entity(
        client,
        "project",
        "demo",
        cascade=True,
    )

    assert result == {"deleted": True}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BEOps.DELETE,
            route_args=base_entity_ra("project", "demo"),
            params={"cascade": True},
        )
    )
