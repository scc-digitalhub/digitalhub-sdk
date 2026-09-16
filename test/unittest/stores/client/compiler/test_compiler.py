import pytest

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import ApiType, BEOps, HttpMethod, OpsType
from digitalhub.stores.client.compiler.compiler import BackendOperationCompiler
from digitalhub.stores.client.compiler.operation import ClientOp


@pytest.mark.parametrize(
    ("operation", "route_args", "params", "method", "api", "request_params", "operation_type"),
    [
        (
            BEOps.SHARE_READ,
            {"entity_type": "project", "entity_name": "demo"},
            {},
            HttpMethod.GET,
            "/api/v1/projects/demo/share",
            {},
            OpsType.ENTITY_READ,
        ),
        (
            BEOps.UNSHARE,
            {"entity_type": "project", "entity_name": "demo"},
            {"user": "alice", "unshare": True, "id": "share-id"},
            HttpMethod.DELETE,
            "/api/v1/projects/demo/share",
            {"user": "alice", "id": "share-id"},
            OpsType.ENTITY_DELETE,
        ),
        (
            BEOps.DATA_READ,
            {"project": "demo", "entity_type": "secret"},
            {"params": {"key": "value"}},
            HttpMethod.GET,
            "/api/v1/-/demo/secrets/data",
            {"key": "value"},
            OpsType.ENTITY_READ,
        ),
        (
            BEOps.READ_ALL_VERSIONS,
            {"project": "demo", "entity_type": "artifact"},
            {"name": "dataset"},
            HttpMethod.GET,
            "/api/v1/-/demo/artifacts",
            {"name": "dataset", "versions": "all"},
            OpsType.ENTITY_LIST,
        ),
    ],
)
def test_compile_resolves_operation_aliases(
    operation,
    route_args,
    params,
    method,
    api,
    request_params,
    operation_type,
) -> None:
    request = ClientOp(
        category=ApiType.BASE if operation in {BEOps.SHARE_READ, BEOps.UNSHARE} else ApiType.CONTEXT,
        operation=operation,
        route_args=route_args,
        params=params,
    )

    compiled = BackendOperationCompiler().compile(request)

    assert compiled.method == method.value
    assert compiled.api == api.replace("/api/v1", get_client_config().api_base, 1)
    assert compiled.params == request_params
    assert compiled.operation == operation_type.value
