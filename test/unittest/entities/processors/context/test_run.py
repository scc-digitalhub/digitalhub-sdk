from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.run as run_module
from digitalhub.entities._processors.context.run import ContextEntityRunProcessor
from digitalhub.entities.log._base.entity import Log
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
from digitalhub.utils.generic_utils import encode_string


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    api = object()
    client.build_api.return_value = api
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, api


def test_read_run_logs_builds_logs_and_decodes_content(monkeypatch) -> None:
    context, client, api = _context()
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
    client.read_object.return_value = logs
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
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.LOGS.value,
        project="context-project",
        entity_type="run",
        entity_id="run-id",
    )
    client.read_object.assert_called_once_with(api, state="READY")


def test_stop_entity_creates_backend_operation(monkeypatch) -> None:
    context, client, api = _context()
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))

    result = ContextEntityRunProcessor().stop_entity("project", "run", "run-id", reason="cancelled")

    assert result is None
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.STOP.value,
        project="context-project",
        entity_type="run",
        entity_id="run-id",
    )
    client.create_object.assert_called_once_with(api, obj={}, reason="cancelled")


def test_resume_entity_creates_backend_operation(monkeypatch) -> None:
    context, client, api = _context()
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))

    result = ContextEntityRunProcessor().resume_entity("project", "run", "run-id", reason="retry")

    assert result is None
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.RESUME.value,
        project="context-project",
        entity_type="run",
        entity_id="run-id",
    )
    client.create_object.assert_called_once_with(api, obj={}, reason="retry")
