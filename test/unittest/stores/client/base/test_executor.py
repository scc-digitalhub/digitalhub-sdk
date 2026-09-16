from unittest.mock import Mock

import pytest

import digitalhub.stores.client.executor.executor as executor_module
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import ApiType, BEOps, OpsType
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.executor.executor import ClientOpExecutor
from digitalhub.stores.client.http.request import BERequest
from digitalhub.utils.exceptions import BackendError


@pytest.fixture
def executor(monkeypatch) -> tuple[ClientOpExecutor, Mock, Mock]:
    compiler = Mock()
    http_handler = Mock()
    compiler.compile.return_value = BERequest(method="GET", api="/artifacts", params={})
    monkeypatch.setattr(executor_module, "BackendOperationCompiler", Mock(return_value=compiler))
    return ClientOpExecutor(http_handler), compiler, http_handler


def test_execute_first_stops_after_first_non_empty_page(executor) -> None:
    client_executor, compiler, http_handler = executor
    http_handler.execute_request.return_value = {"content": [{"id": "first"}, {"id": "second"}], "totalPages": 3}
    operation = ClientOp(category=ApiType.CONTEXT, operation=BEOps.LIST)

    result = client_executor.execute_first(operation)

    assert result == {"id": "first"}
    compiler.compile.assert_called_once_with(operation)
    http_handler.execute_request.assert_called_once()


def test_execute_first_raises_for_empty_pages(executor) -> None:
    client_executor, _, http_handler = executor
    http_handler.execute_request.return_value = {"content": [], "totalPages": 1}

    with pytest.raises(BackendError, match="No object found"):
        client_executor.execute_first(ClientOp(category=ApiType.CONTEXT, operation=BEOps.LIST))


def test_get_k8s_resource_profiles_uses_http_handler(executor) -> None:
    client_executor, _, http_handler = executor
    http_handler.execute_request.return_value = {
        get_client_config().k8s_resource_profiles: ["gpu", "cpu"],
    }

    result = client_executor.get_k8s_resource_profiles()

    assert result == ["gpu", "cpu"]
    http_handler.execute_request.assert_called_once_with(
        BERequest(
            method="GET",
            api=get_client_config().well_known_conf,
            operation=OpsType.CONFIG_K8S_RESOURCE_PROFILES,
        )
    )
