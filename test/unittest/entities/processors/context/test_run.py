from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.run as run_module
from digitalhub.entities._processors.context.run import ContextEntityRunProcessor
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    api = object()
    client.build_api.return_value = api
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, api


def test_read_run_logs_builds_logs_and_decodes_content(monkeypatch) -> None:
    context, client, api = _context()
    logs = [{"key": "log-key", "content": "encoded-content"}, {"key": "other-key"}]
    client.read_object.return_value = logs
    log_entities = [Mock(), Mock()]
    build_entity = Mock(side_effect=log_entities)
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))
    monkeypatch.setattr(run_module.entity_factory, "build_entity_from_dict", build_entity)

    result = ContextEntityRunProcessor().read_run_logs(
        "project",
        "run",
        "run-id",
        state="READY",
    )

    assert result == log_entities
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.LOGS.value,
        project="context-project",
        entity_type="run",
        entity_id="run-id",
    )
    client.read_object.assert_called_once_with(api, state="READY")
    build_entity.assert_any_call({"key": "log-key", "kind": "log"})
    build_entity.assert_any_call({"key": "other-key", "kind": "log"})
    log_entities[0].set_content.assert_called_once_with("encoded-content")
    log_entities[1].set_content.assert_called_once_with(None)
    assert logs == [{"key": "log-key", "kind": "log"}, {"key": "other-key", "kind": "log"}]


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
