# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock, call

import pytest

import digitalhub.entities.project._base.processor as special_ops_module
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import NoOptions, ShareOptions
from digitalhub.stores.client.compiler.targets import BaseEntityTarget


def test_unshare_finds_user_after_first_acl_entry(monkeypatch) -> None:
    client = Mock()
    client.execute.side_effect = [
        [
            {"id": "alice-id", "user": "alice"},
            {"id": "bob-id", "user": "bob"},
        ],
        None,
    ]
    monkeypatch.setattr(special_ops_module, "resolve_client", Mock(return_value=client))

    ProjectProcessor().share_project_entity(
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
    monkeypatch.setattr(special_ops_module, "resolve_client", Mock(return_value=client))

    result = ProjectProcessor().share_project_entity(
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
    monkeypatch.setattr(special_ops_module, "resolve_client", Mock(return_value=client))

    with pytest.raises(ValueError, match="User 'bob' does not have access to project"):
        ProjectProcessor().share_project_entity(
            entity_type="project",
            entity_name="example",
            user="bob",
            unshare=True,
        )
