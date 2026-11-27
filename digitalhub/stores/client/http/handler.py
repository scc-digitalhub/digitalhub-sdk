# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from dataclasses import replace
from typing import Any

from digitalhub.stores.client.common.config import ClientConfig
from digitalhub.stores.client.common.utils import with_default_timeout
from digitalhub.stores.client.http.response import ResponseProcessor
from digitalhub.utils.exceptions import UnauthorizedError
from digitalhub.utils.uri_utils import has_remote_scheme

if typing.TYPE_CHECKING:
    from requests import Response

    from digitalhub.stores.client.auth.provider import AuthProvider
    from digitalhub.stores.client.http.request import BackendReq
    from digitalhub.stores.client.http.transport import HttpTransport


class HttpRequestHandler:
    """
    Handles HTTP request execution for DHCore client.

    Encapsulates all HTTP communication logic including request execution,
    automatic token refresh on authentication failures, and response processing.
    Works in coordination with an auth provider for authentication and response
    processor for parsing.
    """

    def __init__(
        self,
        auth: AuthProvider,
        transport: HttpTransport,
        config: ClientConfig | None = None,
    ) -> None:
        self._auth = auth
        self._transport = transport
        self._config = config if config is not None else ClientConfig()
        self._response_processor = ResponseProcessor()

    def execute_request(self, backend_request: BackendReq) -> Any:
        """Execute API call with full URL construction and authentication."""
        return self._execute_request(self._prepare(backend_request))

    def send(self, backend_request: BackendReq) -> Response:
        """
        Send a request and return the response without processing it.

        Like the other requests, a 401 refreshes the credentials and the
        request is retried once.
        """
        backend_request = self._prepare(backend_request)
        response = self._transport.execute(backend_request)
        if response.status_code == 401 and self._auth.invalidate(backend_request):
            response = self._transport.execute(
                self._auth.authenticate(backend_request),
                attempt=2,
                retry_reason="unauthorized",
            )
        return response

    def _prepare(self, backend_request: BackendReq) -> BackendReq:
        """Authenticate the request, prefix the endpoint to its path and set the default timeout."""
        if backend_request.authenticate:
            backend_request = self._auth.authenticate(backend_request)
        api = backend_request.api
        api = api if has_remote_scheme(api) else f"{self._auth.get_endpoint()}{api}"
        return with_default_timeout(replace(backend_request, api=api), self._config.http_timeout)

    def _execute_request(
        self,
        backend_request: BackendReq,
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
            if retry_on_unauthorized and self._auth.invalidate(backend_request):
                retry_request = self._auth.authenticate(backend_request)
                return self._execute_request(
                    retry_request,
                    retry_on_unauthorized=False,
                    attempt=attempt + 1,
                    retry_reason="unauthorized",
                )
            raise
