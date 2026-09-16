# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.base.special_ops as special_ops_module
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import NoOptions, ShareOptions
from digitalhub.stores.client.compiler.targets import BaseEntityTarget


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
                operation=BackendOp.SHARE_READ,
                target=BaseEntityTarget("project", "example"),
                options=NoOptions(),
            )
        ),
        call(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.UNSHARE,
                target=BaseEntityTarget("project", "example"),
                options=ShareOptions(user="bob", unshare=True, share_id="bob-id"),
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
            operation=BackendOp.SHARE,
            target=BaseEntityTarget("project", "example"),
            options=ShareOptions(user="alice", role="reader"),
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
