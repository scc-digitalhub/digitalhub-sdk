# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.secret as secret_module
from digitalhub.entities._processors.context.secret import ContextEntitySecretProcessor
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
    client.execute.return_value = {"value": "secret"}
    monkeypatch.setattr(secret_module, "get_context", Mock(return_value=context))

    result = ContextEntitySecretProcessor().read_secret_data(
        "project",
        "secret",
        params={"keys": "token"},
    )

    assert result == {"value": "secret"}
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
    data = {"value": "secret"}

    result = ContextEntitySecretProcessor().update_secret_data(
        "project",
        "secret",
        data,
    )

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.DATA_UPDATE,
            target=ContextCollectionTarget("project", "secret"),
            options=NoOptions(),
            payload=data,
        )
    )
