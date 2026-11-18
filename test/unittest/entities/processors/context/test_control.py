# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.control as control_module
from digitalhub.entities._processors.context.control import ContextEntityControlProcessor
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import StopResumeOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget


def test_stop_entity_creates_backend_operation(monkeypatch) -> None:
    client = Mock()
    monkeypatch.setattr(control_module, "get_context", Mock(return_value=SimpleNamespace(client=client)))

    result = ContextEntityControlProcessor().stop_entity("project", "trigger", "trigger-id", reason="cancelled")

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.STOP,
            target=ContextEntityTarget("project", "trigger", "trigger-id"),
            payload={},
            options=StopResumeOptions(reason="cancelled"),
        )
    )


def test_resume_entity_creates_backend_operation(monkeypatch) -> None:
    client = Mock()
    monkeypatch.setattr(control_module, "get_context", Mock(return_value=SimpleNamespace(client=client)))

    result = ContextEntityControlProcessor().resume_entity("project", "run", "run-id", reason="retry")

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.RESUME,
            target=ContextEntityTarget("project", "run", "run-id"),
            payload={},
            options=StopResumeOptions(reason="retry"),
        )
    )
