# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

import digitalhub.stores.client.executor.executor as executor_module
from digitalhub.stores.client.common.constants import K8S_RESOURCE_PROFILES_KEY, WELL_KNOWN_CONFIGURATION
from digitalhub.stores.client.common.enums import ApiType, BackendOp, OpsType
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import ContextCollectionTarget
from digitalhub.stores.client.executor.executor import ClientOpExecutor
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.exceptions import BackendError


@pytest.fixture
def executor(monkeypatch) -> tuple[ClientOpExecutor, Mock, Mock]:
    compiler = Mock()
    http_handler = Mock()
    compiler.compile.return_value = BackendReq(method="GET", api="/artifacts", params={})
    monkeypatch.setattr(executor_module, "BackendOperationCompiler", Mock(return_value=compiler))
    return ClientOpExecutor(http_handler), compiler, http_handler


def test_execute_first_stops_after_first_non_empty_page(executor) -> None:
    client_executor, compiler, http_handler = executor
    http_handler.execute_request.return_value = {"content": [{"id": "first"}, {"id": "second"}], "totalPages": 3}
    operation = ClientOp(
        category=ApiType.CONTEXT,
        operation=BackendOp.LIST,
        target=ContextCollectionTarget("demo", "artifact"),
    )

    result = client_executor.execute_first(operation)

    assert result == {"id": "first"}
    compiler.compile.assert_called_once_with(operation)
    http_handler.execute_request.assert_called_once()


def test_execute_first_raises_for_empty_pages(executor) -> None:
    client_executor, _, http_handler = executor
    http_handler.execute_request.return_value = {"content": [], "totalPages": 1}

    with pytest.raises(BackendError, match="No object found"):
        client_executor.execute_first(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.LIST,
                target=ContextCollectionTarget("demo", "artifact"),
            )
        )


def test_iter_list_yields_paginated_results_lazily(executor) -> None:
    client_executor, compiler, http_handler = executor
    http_handler.execute_request.side_effect = [
        {"content": [{"id": "first"}], "totalPages": 2},
        {"content": [{"id": "second"}], "totalPages": 2},
    ]
    operation = ClientOp(
        category=ApiType.CONTEXT,
        operation=BackendOp.LIST,
        target=ContextCollectionTarget("demo", "artifact"),
    )

    results = client_executor.iter_list(operation)

    compiler.compile.assert_not_called()
    assert next(results) == {"id": "first"}
    compiler.compile.assert_called_once_with(operation)
    http_handler.execute_request.assert_called_once()
    assert list(results) == [{"id": "second"}]
    assert http_handler.execute_request.call_count == 2


def test_execute_list_collects_all_pages(executor) -> None:
    client_executor, compiler, http_handler = executor
    http_handler.execute_request.side_effect = [
        {"content": [{"id": "first"}], "totalPages": 2},
        {"content": [{"id": "second"}], "totalPages": 2},
    ]
    operation = ClientOp(
        category=ApiType.CONTEXT,
        operation=BackendOp.LIST,
        target=ContextCollectionTarget("demo", "artifact"),
    )

    assert client_executor.execute_list(operation) == [{"id": "first"}, {"id": "second"}]
    compiler.compile.assert_called_once_with(operation)
    assert http_handler.execute_request.call_count == 2


def test_get_k8s_resource_profiles_uses_http_handler(executor) -> None:
    client_executor, _, http_handler = executor
    http_handler.execute_request.return_value = {
        K8S_RESOURCE_PROFILES_KEY: ["gpu", "cpu"],
    }

    result = client_executor.get_k8s_resource_profiles()

    assert result == ["gpu", "cpu"]
    http_handler.execute_request.assert_called_once_with(
        BackendReq(
            method="GET",
            api=WELL_KNOWN_CONFIGURATION,
            operation=OpsType.CONFIG_K8S_RESOURCE_PROFILES,
        )
    )
