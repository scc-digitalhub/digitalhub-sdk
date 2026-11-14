# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
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
    if not logger.isEnabledFor(logging.DEBUG):
        return

    template = (
        "Request: Operation: %s - Attempt: %s - Retry reason: %s - "
        "HTTP %s %s - "
        "Status: %s - "
        "Headers: %s - "
        "Request body: %s - "
        "Response body: %s"
    )
    logger.debug(
        template,
        operation,
        attempt,
        retry_reason or "none",
        response.request.method,
        response.url,
        response.status_code,
        dict(response.request.headers),
        response.request.body,
        response.text,
    )
