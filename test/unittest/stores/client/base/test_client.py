# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

import digitalhub.stores.client.client as client_module
import digitalhub.stores.client.compiler.compiler as compiler_module
from digitalhub.stores.client.client import Client
from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import DeleteAllVersionsOptions, OpaqueOptions
from digitalhub.stores.client.compiler.params.profile import ParamsProfile
from digitalhub.stores.client.compiler.targets import BaseCollectionTarget, ContextCollectionTarget
from digitalhub.stores.client.http.request import BackendReq


@pytest.fixture
def client_with_handler(monkeypatch):
    configurator = Mock()
    api_builder = Mock()
    params_builder = Mock()
    transport = Mock()
    http_handler = Mock()

    configurator_factory = Mock(return_value=configurator)
    handler_factory = Mock(return_value=http_handler)
    monkeypatch.setattr(client_module, "HttpTransport", Mock(return_value=transport))
    monkeypatch.setattr(client_module, "ClientConfigurator", configurator_factory)
    monkeypatch.setattr(compiler_module, "ClientApiBuilder", lambda: api_builder)
    monkeypatch.setattr(compiler_module, "ClientParametersBuilder", lambda: params_builder)
    monkeypatch.setattr(client_module, "HttpRequestHandler", handler_factory)

    client = Client()
    return (
        client,
        configurator,
        api_builder,
        params_builder,
        transport,
        http_handler,
        configurator_factory,
        handler_factory,
    )


def test_client_builds_shared_transport(client_with_handler) -> None:
    _, configurator, _, _, transport, _, configurator_factory, handler_factory = client_with_handler

    client_module.HttpTransport.assert_called_once_with()
    configurator_factory.assert_called_once_with(transport)
    handler_factory.assert_called_once_with(configurator, transport)


def test_client_operation_contains_only_semantic_request_data() -> None:
    request = ClientOp(
        category=ApiType.BASE,
        operation=BackendOp.CREATE,
        target=BaseCollectionTarget("project"),
        options=OpaqueOptions({"state": "READY"}),
        payload={"name": "demo"},
    )

    assert request.target == BaseCollectionTarget("project")
    assert request.options == OpaqueOptions({"state": "READY"})
    assert request.payload == {"name": "demo"}

    with pytest.raises(FrozenInstanceError):
        request.target.entity_type = "other"

    with pytest.raises(TypeError):
        ClientOp(
            category=ApiType.BASE,
            operation=BackendOp.CREATE,
            timeout=4,
        )


def test_execute_compiles_backend_operation_request(client_with_handler) -> None:
    client, _, api_builder, params_builder, _, http_handler, _, _ = client_with_handler
    api_builder.build_api.return_value = "/projects"
    params_builder.build_parameters.return_value = {"params": {"state": "READY"}}
    http_handler.execute_request.return_value = {"name": "demo"}
    request = ClientOp(
        category=ApiType.BASE,
        operation=BackendOp.CREATE,
        target=BaseCollectionTarget("project"),
        options=OpaqueOptions({"state": "READY"}),
        payload={"name": "demo"},
    )

    result = client.execute(request)

    assert result == {"name": "demo"}
    api_builder.build_api.assert_called_once_with(
        ApiType.BASE,
        BackendOp.CREATE,
        BaseCollectionTarget("project"),
    )
    params_builder.build_parameters.assert_not_called()
    http_handler.execute_request.assert_called_once_with(
        BackendReq(
            method="POST",
            api="/projects",
            operation="entity.create",
            params={"state": "READY"},
            headers={"Content-Type": "application/json"},
            data='{"name": "demo"}',
        )
    )


def test_execute_compiles_delete_all_versions(client_with_handler) -> None:
    client, _, api_builder, params_builder, _, http_handler, _, _ = client_with_handler
    api_builder.build_api.return_value = "/projects"
    params_builder.build_parameters.return_value = {
        "params": {"name": "demo", "cascade": "true"},
    }
    http_handler.execute_request.return_value = {"deleted": True}
    request = ClientOp(
        category=ApiType.CONTEXT,
        operation=BackendOp.DELETE_ALL_VERSIONS,
        target=ContextCollectionTarget("demo", "artifact"),
        options=DeleteAllVersionsOptions(name="artifact", cascade=True),
    )

    result = client.execute(request)

    assert result == {"deleted": True}
    params_builder.build_parameters.assert_called_once_with(
        ApiType.CONTEXT,
        ParamsProfile.DELETE_ALL_VERSIONS,
        DeleteAllVersionsOptions(name="artifact", cascade=True),
    )
    http_handler.execute_request.assert_called_once_with(
        BackendReq(
            method="DELETE",
            api="/projects",
            operation="entity.delete",
            params={"name": "demo", "cascade": "true"},
        )
    )


def test_get_k8s_resource_profiles_uses_the_http_handler(client_with_handler) -> None:
    client, _, _, _, _, http_handler, _, _ = client_with_handler
    http_handler.execute_request.return_value = {
        get_client_config().k8s_resource_profiles: ["gpu", "cpu"],
    }

    result = client.get_k8s_resource_profiles()

    assert result == ["gpu", "cpu"]
    http_handler.execute_request.assert_called_once_with(
        BackendReq(
            method="GET",
            api=get_client_config().well_known_conf,
            operation="config.k8s_resource_profiles",
        )
    )
