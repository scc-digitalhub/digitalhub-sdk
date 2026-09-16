# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from requests import request as requests_request
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

    @staticmethod
    def _request(method: str, url: str, **kwargs) -> Response:
        """Execute an HTTP request and normalize transport errors."""
        try:
            return requests_request(method, url, **kwargs)
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
