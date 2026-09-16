# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client.common.enums import OpsType

if typing.TYPE_CHECKING:
    from logging import Logger

    from requests import Response


def log_request_response(
    logger: Logger,
    response: Response,
    *,
    operation: str = OpsType.HTTP_REQUEST.value,
    attempt: int = 1,
    retry_reason: str | None = None,
) -> None:
    """
    Log HTTP request and response details at DEBUG level.
    """
    template = (
        "Request: Operation: {operation} - Attempt: {attempt} - Retry reason: {retry_reason} - "
        "HTTP {method} {url} - "
        "Status: {status_code} - "
        "Headers: {request_headers} - "
        "Request body: {request_body} - "
        "Response body: {response_body}"
    )
    logger.debug(
        template.format(
            operation=operation,
            attempt=attempt,
            retry_reason=retry_reason or "none",
            method=response.request.method,
            url=response.url,
            status_code=response.status_code,
            request_headers=dict(response.request.headers),
            request_body=response.request.body,
            response_body=response.text,
        ),
    )
