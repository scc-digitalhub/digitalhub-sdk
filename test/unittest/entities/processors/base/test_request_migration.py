# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import DeleteOptions, NoOptions
from digitalhub.stores.client.compiler.targets import BaseCollectionTarget, BaseEntityTarget


def test_create_base_entity_uses_backend_operation_request() -> None:
    client = Mock()
    client.execute.return_value = {"id": "project-id"}
    entity = {"name": "demo"}

    result = BaseEntityCRUDProcessor()._create_base_entity(client, "project", entity)

    assert result == {"id": "project-id"}
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.CREATE,
            target=BaseCollectionTarget("project"),
            options=NoOptions(),
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
            operation=BackendOp.READ,
            target=BaseEntityTarget("project", "demo"),
            options=NoOptions(),
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
            operation=BackendOp.LIST,
            target=BaseCollectionTarget("project"),
            options=NoOptions(),
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
            operation=BackendOp.UPDATE,
            target=BaseEntityTarget("project", "demo"),
            options=NoOptions(),
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
            operation=BackendOp.DELETE,
            target=BaseEntityTarget("project", "demo"),
            options=DeleteOptions(cascade=True),
        )
    )
