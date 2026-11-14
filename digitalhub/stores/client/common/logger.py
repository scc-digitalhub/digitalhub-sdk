# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import logging
import typing
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from digitalhub.stores.client.common.enums import OpsType
from digitalhub.stores.client.common.redaction import REDACTED, redact_dict, redact_headers

if typing.TYPE_CHECKING:
    from logging import Logger

    from requests import Response

MAX_LOG_BODY_LENGTH = 4096
_BODY_OMITTED = "<body omitted>"
_TRUNCATION_MARKER = "...<truncated>"


def _operation_value(operation: str | OpsType) -> str:
    return operation.value if isinstance(operation, OpsType) else operation


def _safe_url(url: str) -> str:
    parsed_url = urlsplit(url)
    safe_query = urlencode(
        [(key, redact_dict({key: value})[key]) for key, value in parse_qsl(parsed_url.query, keep_blank_values=True)]
    )
    safe_netloc = parsed_url.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parsed_url.scheme, safe_netloc, parsed_url.path, safe_query, ""))


def _should_omit_bodies(operation: str | OpsType, url: str) -> bool:
    if _operation_value(operation) == OpsType.AUTH_REFRESH.value:
        return True
    return "secrets" in {segment.casefold() for segment in urlsplit(url).path.split("/") if segment}


def _truncate_body(body: str) -> str:
    if len(body) <= MAX_LOG_BODY_LENGTH:
        return body
    return body[: MAX_LOG_BODY_LENGTH - len(_TRUNCATION_MARKER)] + _TRUNCATION_MARKER


def _format_body(body: Any, content_type: str) -> str:
    if body is None:
        return "<empty>"
    if isinstance(body, Mapping):
        return _truncate_body(json.dumps(redact_dict(body), ensure_ascii=False, separators=(",", ":")))
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if not isinstance(body, str) or not body:
        return _BODY_OMITTED

    if "application/x-www-form-urlencoded" in content_type.casefold():
        pairs = parse_qsl(body, keep_blank_values=True)
        safe_pairs = [(key, redact_dict({key: value})[key]) for key, value in pairs]
        return _truncate_body(urlencode(safe_pairs))

    try:
        parsed_body = json.loads(body)
    except json.JSONDecodeError:
        return _BODY_OMITTED
    if not isinstance(parsed_body, dict):
        return _BODY_OMITTED
    return _truncate_body(json.dumps(redact_dict(parsed_body), ensure_ascii=False, separators=(",", ":")))


def log_request_response(
    logger: Logger,
    response: Response,
    *,
    operation: str | OpsType = OpsType.HTTP_REQUEST,
    attempt: int = 1,
    retry_reason: str | None = None,
) -> None:
    """
    Log HTTP request and response details at DEBUG level.
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return
    operation_name = _operation_value(operation)
    safe_url = _safe_url(response.url)
    if _should_omit_bodies(operation, response.url):
        request_body = REDACTED
        response_body = REDACTED
    else:
        request_body = _format_body(
            response.request.body,
            response.request.headers.get("Content-Type", ""),
        )
        response_body = _format_body(
            response.text,
            response.headers.get("Content-Type", ""),
        )

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
        operation_name,
        attempt,
        retry_reason or "none",
        response.request.method,
        safe_url,
        response.status_code,
        redact_headers(response.request.headers),
        request_body,
        response_body,
    )
