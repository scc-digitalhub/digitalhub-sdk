# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from digitalhub.stores.client.common.enums import ApiType, BEOps, HttpMethod, OpsType
from digitalhub.stores.client.common.utils import with_data, with_json_content_type
from digitalhub.stores.client.compiler.apis.api import ClientApiBuilder
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.params.builder import ClientParametersBuilder
from digitalhub.stores.client.http.request import BERequest
from digitalhub.utils.generic_utils import dump_json


@dataclass(frozen=True, slots=True)
class OpsSpec:
    """HTTP and builder semantics for one backend operation."""

    method: HttpMethod
    operation_type: OpsType
    backend_operation: BEOps | None = None
    params_operation: BEOps | None = None


class BackendOperationCompiler:
    """Compile semantic backend operations into immutable HTTP requests."""

    _OPERATION_SPECS: ClassVar[dict[BEOps, OpsSpec]] = {
        BEOps.CREATE: OpsSpec(HttpMethod.POST, OpsType.ENTITY_CREATE),
        BEOps.READ: OpsSpec(HttpMethod.GET, OpsType.ENTITY_READ),
        BEOps.READ_ALL_VERSIONS: OpsSpec(
            HttpMethod.GET,
            OpsType.ENTITY_LIST,
            backend_operation=BEOps.LIST,
            params_operation=BEOps.READ_ALL_VERSIONS,
        ),
        BEOps.UPDATE: OpsSpec(HttpMethod.PUT, OpsType.ENTITY_UPDATE),
        BEOps.DELETE: OpsSpec(HttpMethod.DELETE, OpsType.ENTITY_DELETE),
        BEOps.DELETE_ALL_VERSIONS: OpsSpec(HttpMethod.DELETE, OpsType.ENTITY_DELETE),
        BEOps.LIST: OpsSpec(HttpMethod.GET, OpsType.ENTITY_LIST),
        BEOps.LIST_FIRST: OpsSpec(HttpMethod.GET, OpsType.ENTITY_LIST),
        BEOps.SEARCH: OpsSpec(HttpMethod.GET, OpsType.ENTITY_SEARCH),
        BEOps.STOP: OpsSpec(HttpMethod.POST, OpsType.ENTITY_CREATE),
        BEOps.RESUME: OpsSpec(HttpMethod.POST, OpsType.ENTITY_CREATE),
        BEOps.SHARE: OpsSpec(HttpMethod.POST, OpsType.ENTITY_CREATE),
        BEOps.SHARE_READ: OpsSpec(
            HttpMethod.GET,
            OpsType.ENTITY_READ,
            backend_operation=BEOps.SHARE,
            params_operation=BEOps.READ,
        ),
        BEOps.UNSHARE: OpsSpec(
            HttpMethod.DELETE,
            OpsType.ENTITY_DELETE,
            backend_operation=BEOps.SHARE,
        ),
        BEOps.DATA_READ: OpsSpec(
            HttpMethod.GET,
            OpsType.ENTITY_READ,
            backend_operation=BEOps.DATA,
        ),
        BEOps.DATA_UPDATE: OpsSpec(
            HttpMethod.PUT,
            OpsType.ENTITY_UPDATE,
            backend_operation=BEOps.DATA,
        ),
        BEOps.FILES_READ: OpsSpec(
            HttpMethod.GET,
            OpsType.ENTITY_READ,
            backend_operation=BEOps.FILES,
        ),
        BEOps.FILES_UPDATE: OpsSpec(
            HttpMethod.PUT,
            OpsType.ENTITY_UPDATE,
            backend_operation=BEOps.FILES,
        ),
        BEOps.LOGS_READ: OpsSpec(
            HttpMethod.GET,
            OpsType.ENTITY_READ,
            backend_operation=BEOps.LOGS,
        ),
        BEOps.METRICS_READ: OpsSpec(
            HttpMethod.GET,
            OpsType.ENTITY_READ,
            backend_operation=BEOps.METRICS,
        ),
        BEOps.METRICS_UPDATE: OpsSpec(
            HttpMethod.PUT,
            OpsType.ENTITY_UPDATE,
            backend_operation=BEOps.METRICS,
        ),
    }

    def __init__(self) -> None:
        self._api_builder = ClientApiBuilder()
        self._params_builder = ClientParametersBuilder()

    def build_api(self, category: ApiType, operation: BEOps, **kwargs) -> str:
        """Build an API endpoint for a semantic operation."""
        return self._api_builder.build_api(category, operation, **kwargs)

    def build_parameters(self, category: ApiType, operation: BEOps, **kwargs) -> dict:
        """Build query parameters for a semantic operation."""
        return self._params_builder.build_parameters(category, operation, **kwargs)

    def compile(self, request: ClientOp) -> BERequest:
        """Compile one semantic operation into an immutable backend request."""
        spec = self._OPERATION_SPECS.get(request.operation)
        if spec is None:
            raise ValueError(f"Unsupported backend operation '{request.operation}'.")

        backend_operation = spec.backend_operation or request.operation
        params_operation = spec.params_operation or backend_operation

        api = self.build_api(
            request.category,
            backend_operation,
            **request.route_args,
        )
        parameters = self.build_parameters(
            request.category,
            params_operation,
            **request.params,
        )
        if set(parameters) != {"params"}:
            raise ValueError("Parameter builder returned unsupported backend request options.")
        backend_request = BERequest.from_http(
            spec.method.value,
            api,
            operation=spec.operation_type,
            params=parameters["params"],
        )
        if request.payload is not None:
            backend_request = with_json_content_type(with_data(backend_request, dump_json(request.payload)))
        return backend_request
