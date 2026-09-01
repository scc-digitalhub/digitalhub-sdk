from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.secret as secret_module
from digitalhub.entities._processors.context.secret import ContextEntitySecretProcessor
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    api = object()
    client.build_api.return_value = api
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, api


def test_read_secret_data_builds_api_and_reads_object(monkeypatch) -> None:
    context, client, api = _context()
    client.read_object.return_value = {"value": "secret"}
    monkeypatch.setattr(secret_module, "get_context", Mock(return_value=context))

    result = ContextEntitySecretProcessor().read_secret_data(
        "project",
        "secret",
        key="token",
    )

    assert result == {"value": "secret"}
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.DATA.value,
        project="context-project",
        entity_type="secret",
    )
    client.read_object.assert_called_once_with(api, key="token")


def test_update_secret_data_builds_api_and_updates_object(monkeypatch) -> None:
    context, client, api = _context()
    monkeypatch.setattr(secret_module, "get_context", Mock(return_value=context))
    data = {"value": "secret"}

    result = ContextEntitySecretProcessor().update_secret_data(
        "project",
        "secret",
        data,
        key="token",
    )

    assert result is None
    client.build_api.assert_called_once_with(
        ApiCategories.CONTEXT.value,
        BackendOperations.DATA.value,
        project="context-project",
        entity_type="secret",
    )
    client.update_object.assert_called_once_with(api, data, key="token")
