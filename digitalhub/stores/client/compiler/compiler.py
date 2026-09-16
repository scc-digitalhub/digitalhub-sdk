# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.common.utils import with_data, with_json_content_type
from digitalhub.stores.client.compiler.apis.api import ClientApiBuilder
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import OperationOptions
from digitalhub.stores.client.compiler.params.builder import ClientParametersBuilder
from digitalhub.stores.client.compiler.params.profile import ParamsProfile
from digitalhub.stores.client.compiler.registry import get_operation_spec
from digitalhub.stores.client.compiler.targets import RouteTarget
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.generic_utils import dump_json


class BackendOperationCompiler:
    """Compile semantic backend operations into immutable HTTP requests."""

    def __init__(self) -> None:
        self._api_builder = ClientApiBuilder()
        self._params_builder = ClientParametersBuilder()

    def build_api(self, category: ApiType, operation: BackendOp, target: RouteTarget) -> str:
        """Build an API endpoint for a semantic operation."""
        return self._api_builder.build_api(category, operation, target)

    def build_parameters(self, category: ApiType, profile: ParamsProfile, options: OperationOptions) -> dict:
        """Build query parameters for a semantic operation."""
        return self._params_builder.build_parameters(category, profile, options)

    def compile(self, request: ClientOp) -> BackendReq:
        """Compile one semantic operation into an immutable backend request."""
        spec = get_operation_spec(request.operation)

        api = self.build_api(
            request.category,
            spec.route_operation,
            request.target,
        )
        if spec.params_profile is None:
            params = request.options.to_values()
        else:
            parameters = self.build_parameters(
                request.category,
                spec.params_profile,
                request.options,
            )
            if set(parameters) != {"params"}:
                raise ValueError("Parameter builder returned unsupported backend request options.")
            params = parameters["params"]
        backend_request = BackendReq.from_http(
            spec.method.value,
            api,
            operation=spec.operation_type,
            params=params,
        )
        if request.payload is not None:
            backend_request = with_json_content_type(with_data(backend_request, dump_json(request.payload)))
        return backend_request
