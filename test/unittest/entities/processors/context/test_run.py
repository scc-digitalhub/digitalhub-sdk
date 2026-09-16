# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.run as run_module
from digitalhub.entities._processors.context.run import ContextEntityRunProcessor
from digitalhub.entities.log._base.entity import Log
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions, StopResumeOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.generic_utils import encode_string


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, object()


def test_read_run_logs_builds_logs_and_decodes_content(monkeypatch) -> None:
    context, client, _ = _context()
    logs = [
        {
            "project": "project",
            "name": "run-log",
            "id": "log-id",
            "spec": {"run": "run-id"},
            "content": encode_string("run finished"),
        },
        {
            "project": "project",
            "name": "other-log",
            "id": "other-id",
            "spec": {"run": "run-id"},
        },
    ]
    client.execute.return_value = logs
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))

    result = ContextEntityRunProcessor().read_run_logs(
        "project",
        "run",
        "run-id",
        state="READY",
    )

    assert all(isinstance(log, Log) for log in result)
    assert [log.kind for log in result] == ["log", "log"]
    assert [log.text for log in result] == ["run finished", None]
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.LOGS_READ,
            target=ContextEntityTarget("project", "run", "run-id"),
            options=LogsOptions(state="READY"),
        )
    )


def test_stop_entity_creates_backend_operation(monkeypatch) -> None:
    context, client, _ = _context()
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))

    result = ContextEntityRunProcessor().stop_entity("project", "run", "run-id", reason="cancelled")

    assert result is None
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.STOP,
            target=ContextEntityTarget("project", "run", "run-id"),
            payload={},
            options=StopResumeOptions(reason="cancelled"),
        )
    )


def test_resume_entity_creates_backend_operation(monkeypatch) -> None:
    context, client, _ = _context()
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))

    result = ContextEntityRunProcessor().resume_entity("project", "run", "run-id", reason="retry")

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
