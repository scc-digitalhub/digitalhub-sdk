# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.secret._base.processor as secret_module
from digitalhub.entities.secret._base.processor import SecretProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import NoOptions, OpaqueOptions
from digitalhub.stores.client.compiler.targets import ContextCollectionTarget


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, object()


def test_read_secret_data_uses_backend_operation_request(monkeypatch) -> None:
    context, client, _ = _context()
    client.execute.return_value = {"token": "secret"}
    monkeypatch.setattr(secret_module, "get_context", Mock(return_value=context))
    entity = SimpleNamespace(
        project="project",
        ENTITY_TYPE="secret",
        name="token",
    )

    result = SecretProcessor().read_secret_value(entity)

    assert result == "secret"
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.DATA_READ,
            target=ContextCollectionTarget("project", "secret"),
            options=OpaqueOptions({"keys": "token"}),
        )
    )


def test_update_secret_data_uses_backend_operation_request(monkeypatch) -> None:
    context, client, _ = _context()
    monkeypatch.setattr(secret_module, "get_context", Mock(return_value=context))
    entity = SimpleNamespace(
        project="project",
        ENTITY_TYPE="secret",
        name="token",
    )

    result = SecretProcessor().set_secret_value(entity, "secret")

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.DATA_UPDATE,
            target=ContextCollectionTarget("project", "secret"),
            options=NoOptions(),
            payload={"token": "secret"},
        )
    )
