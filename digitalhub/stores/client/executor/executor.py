# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.client.common.constants import K8S_RESOURCE_PROFILES_KEY, WELL_KNOWN_CONFIGURATION
from digitalhub.stores.client.common.enums import OpsType
from digitalhub.stores.client.common.utils import next_page, with_pagination
from digitalhub.stores.client.compiler.compiler import BackendOperationCompiler
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.http.handler import HttpRequestHandler
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.exceptions import BackendError


class ClientOpExecutor:
    """Compile and execute semantic client operations."""

    def __init__(self, http_handler: HttpRequestHandler, config: ClientConfig | None = None) -> None:
        self._compiler = BackendOperationCompiler()
        self._http_handler = http_handler
        self._config = config if config is not None else ClientConfig()

    def execute(self, operation: ClientOp) -> Any:
        """Compile and execute one semantic operation."""
        return self._http_handler.execute_request(self._compiler.compile(operation))

    def execute_list(self, operation: ClientOp) -> list[dict[str, Any]]:
        """Compile and execute a paginated semantic list operation."""
        return list(self.iter_list(operation))

    def iter_list(self, operation: ClientOp) -> Iterator[dict[str, Any]]:
        """Yield objects from a paginated list operation without buffering all pages."""
        request = with_pagination(self._compiler.compile(operation), self._config, partial=True)
        for response in self._iter_paginated_responses(request):
            yield from response["content"]

    def execute_first(self, operation: ClientOp) -> dict[str, Any]:
        """Return the first result without loading subsequent results."""
        request = with_pagination(self._compiler.compile(operation), self._config, partial=True)
        for response in self._iter_paginated_responses(request):
            if response["content"]:
                return response["content"][0]
        raise BackendError("No object found.")

    def get_k8s_resource_profiles(self) -> list[str]:
        """Get Kubernetes resource profiles from the backend configuration."""
        data = self._http_handler.execute_request(
            BackendReq.get(
                api=WELL_KNOWN_CONFIGURATION,
                operation=OpsType.CONFIG_K8S_RESOURCE_PROFILES,
            )
        )
        return data.get(K8S_RESOURCE_PROFILES_KEY, [])

    def _iter_paginated_responses(self, request: BackendReq) -> Iterator[dict[str, Any]]:
        """Yield paginated responses while advancing requests immutably."""
        while True:
            response = self._http_handler.execute_request(request)
            yield response
            if not response["content"] or request.params["page"] >= (response["totalPages"] - 1):
                return
            request = next_page(request)
