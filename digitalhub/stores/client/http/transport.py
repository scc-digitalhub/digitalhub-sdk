# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

from digitalhub.stores.client.common.logger import log_request_response
from digitalhub.stores.client.http.errors import raise_for_transport_error
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from requests import Response

logger = get_logger(__name__)


class HttpTransport:
    """Send absolute backend requests and log their transport responses."""

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.mount("http://", HTTPAdapter(pool_connections=10, pool_maxsize=20))
        self._session.mount("https://", HTTPAdapter(pool_connections=10, pool_maxsize=20))

    def close(self) -> None:
        """Close the underlying HTTP session and its connection pools."""
        self._session.close()

    def _request(self, method: str, url: str, **kwargs) -> Response:
        """Execute an HTTP request and normalize transport errors."""
        try:
            return self._session.request(method, url, **kwargs)
        except RequestException as error:
            raise_for_transport_error(error)

    def execute(
        self,
        backend_request: BackendReq,
        *,
        attempt: int = 1,
        retry_reason: str | None = None,
    ) -> Response:
        response = self._request(
            backend_request.method,
            backend_request.api,
            **backend_request.to_transport_kwargs(),
        )
        log_request_response(
            logger,
            response,
            operation=backend_request.operation,
            attempt=attempt,
            retry_reason=retry_reason,
        )
        return response
