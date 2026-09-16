# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.base.special_ops as special_ops_module
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import base_entity_ra
from digitalhub.stores.client.compiler.operation import ClientOp


def test_build_project_key_uses_store_scheme() -> None:
    assert BaseEntitySpecialOpsProcessor().build_project_key("project-id") == "store://project-id"


def test_unshare_finds_user_after_first_acl_entry(monkeypatch) -> None:
    client = Mock()
    client.execute.side_effect = [
        [
            {"id": "alice-id", "user": "alice"},
            {"id": "bob-id", "user": "bob"},
        ],
        None,
    ]
    monkeypatch.setattr(special_ops_module, "get_client", Mock(return_value=client))

    BaseEntitySpecialOpsProcessor().share_project_entity(
        entity_type="project",
        entity_name="example",
        user="bob",
        unshare=True,
    )

    assert client.execute.call_args_list == [
        call(
            ClientOp(
                category=ApiType.BASE,
                operation=BEOps.SHARE_READ,
                route_args=base_entity_ra("project", "example"),
            )
        ),
        call(
            ClientOp(
                category=ApiType.BASE,
                operation=BEOps.UNSHARE,
                route_args=base_entity_ra("project", "example"),
                params={"unshare": True, "user": "bob", "id": "bob-id"},
            )
        ),
    ]


def test_share_creates_access_with_built_parameters(monkeypatch) -> None:
    client = Mock()
    monkeypatch.setattr(special_ops_module, "get_client", Mock(return_value=client))

    result = BaseEntitySpecialOpsProcessor().share_project_entity(
        entity_type="project",
        entity_name="example",
        user="alice",
        role="reader",
    )

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.BASE,
            operation=BEOps.SHARE,
            route_args=base_entity_ra("project", "example"),
            params={"unshare": False, "user": "alice", "role": "reader"},
            payload={},
        )
    )


def test_unshare_raises_when_user_has_no_access(monkeypatch) -> None:
    client = Mock()
    client.execute.return_value = [{"id": "alice-id", "user": "alice"}]
    monkeypatch.setattr(special_ops_module, "get_client", Mock(return_value=client))

    with pytest.raises(ValueError, match="User 'bob' does not have access to project"):
        BaseEntitySpecialOpsProcessor().share_project_entity(
            entity_type="project",
            entity_name="example",
            user="bob",
            unshare=True,
        )
