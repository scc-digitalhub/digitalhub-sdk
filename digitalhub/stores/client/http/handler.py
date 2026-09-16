# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import replace
from typing import Any

from digitalhub.stores.client.auth.client_configurator import ClientConfigurator
from digitalhub.stores.client.http.request import BERequest
from digitalhub.stores.client.http.response import ResponseProcessor
from digitalhub.stores.client.http.transport import HttpTransport
from digitalhub.utils.exceptions import UnauthorizedError
from digitalhub.utils.uri_utils import has_remote_scheme


class HttpRequestHandler:
    """
    Handles HTTP request execution for DHCore client.

    Encapsulates all HTTP communication logic including request execution,
    automatic token refresh on authentication failures, and response processing.
    Works in coordination with configurator for authentication and response
    processor for parsing.
    """

    def __init__(self, configurator: ClientConfigurator, transport: HttpTransport) -> None:
        self._configurator = configurator
        self._transport = transport
        self._response_processor = ResponseProcessor()

    def execute_request(self, backend_request: BERequest) -> Any:
        """Execute API call with full URL construction and authentication."""
        if backend_request.authenticate:
            backend_request = self._configurator.authenticate(backend_request)
        api = backend_request.api
        api = api if has_remote_scheme(api) else f"{self._configurator.get_endpoint()}{api}"
        backend_request = replace(backend_request, api=api)
        return self._execute_request(backend_request)

    def _execute_request(
        self,
        backend_request: BERequest,
        *,
        retry_on_unauthorized: bool = True,
        attempt: int = 1,
        retry_reason: str | None = None,
    ) -> Any:
        """
        Sends HTTP request with authentication, handles token refresh on 401 errors,
        validates API version compatibility, and parses response.
        """
        response = self._transport.execute(
            backend_request,
            attempt=attempt,
            retry_reason=retry_reason,
        )
        try:
            return self._response_processor.process(response)
        except UnauthorizedError:
            if retry_on_unauthorized and self._configurator.evaluate_refresh():
                retry_request = self._configurator.authenticate(backend_request)
                return self._execute_request(
                    retry_request,
                    retry_on_unauthorized=False,
                    attempt=attempt + 1,
                    retry_reason="unauthorized",
                )
            raise
