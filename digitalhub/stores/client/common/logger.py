# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from logging import Logger

    from requests import Response


def log_request_response(logger: Logger, response: Response) -> None:
    """
    Log HTTP request and response details at DEBUG level.

    Parameters
    ----------
    logger : Logger
        Logger instance to use for logging.
    response : Response
        HTTP response object containing request and response details.
    """
    template = (
        "Request: HTTP {method} {url} - "
        "Status: {status_code} - "
        "Headers: {request_headers} - "
        "Request body: {request_body} - "
        "Response body: {response_body}"
    )
    logger.debug(
        template.format(
            method=response.request.method,
            url=response.url,
            status_code=response.status_code,
            request_headers=dict(response.request.headers),
            request_body=response.request.body,
            response_body=response.text,
        ),
    )
