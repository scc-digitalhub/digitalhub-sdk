from unittest.mock import Mock

import pytest

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import ApiType, BackendOp, HttpMethod, OpsType
from digitalhub.stores.client.compiler.compiler import BackendOperationCompiler
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import NoOptions, OpaqueOptions, ReadAllVersionsOptions, ShareOptions
from digitalhub.stores.client.compiler.targets import BaseCollectionTarget, BaseEntityTarget, ContextCollectionTarget


@pytest.mark.parametrize(
    ("operation", "target", "options", "method", "api", "request_params", "operation_type"),
    [
        (
            BackendOp.SHARE_READ,
            BaseEntityTarget("project", "demo"),
            NoOptions(),
            HttpMethod.GET,
            "/api/v1/projects/demo/share",
            {},
            OpsType.ENTITY_READ,
        ),
        (
            BackendOp.UNSHARE,
            BaseEntityTarget("project", "demo"),
            ShareOptions(user="alice", unshare=True, share_id="share-id"),
            HttpMethod.DELETE,
            "/api/v1/projects/demo/share",
            {"user": "alice", "id": "share-id"},
            OpsType.ENTITY_DELETE,
        ),
        (
            BackendOp.DATA_READ,
            ContextCollectionTarget("demo", "secret"),
            OpaqueOptions({"key": "value"}),
            HttpMethod.GET,
            "/api/v1/-/demo/secrets/data",
            {"key": "value"},
            OpsType.ENTITY_READ,
        ),
        (
            BackendOp.READ_ALL_VERSIONS,
            ContextCollectionTarget("demo", "artifact"),
            ReadAllVersionsOptions(name="dataset"),
            HttpMethod.GET,
            "/api/v1/-/demo/artifacts",
            {"name": "dataset", "versions": "all"},
            OpsType.ENTITY_LIST,
        ),
    ],
)
def test_compile_resolves_operation_aliases(
    operation,
    target,
    options,
    method,
    api,
    request_params,
    operation_type,
) -> None:
    request = ClientOp(
        category=ApiType.BASE if operation in {BackendOp.SHARE_READ, BackendOp.UNSHARE} else ApiType.CONTEXT,
        operation=operation,
        target=target,
        options=options,
    )

    compiled = BackendOperationCompiler().compile(request)

    assert compiled.method == method.value
    assert compiled.api == api.replace("/api/v1", get_client_config().api_base, 1)
    assert compiled.params == request_params
    assert compiled.operation == operation_type.value


def test_compile_passes_through_parameters_without_profile(monkeypatch) -> None:
    compiler = BackendOperationCompiler()
    build_parameters = Mock(side_effect=AssertionError("parameter builder should not be called"))
    monkeypatch.setattr(compiler, "build_parameters", build_parameters)
    request = ClientOp(
        category=ApiType.BASE,
        operation=BackendOp.CREATE,
        target=BaseCollectionTarget("project"),
        options=OpaqueOptions({"state": "READY"}),
    )

    compiled = compiler.compile(request)

    assert compiled.params == {"state": "READY"}
    build_parameters.assert_not_called()
