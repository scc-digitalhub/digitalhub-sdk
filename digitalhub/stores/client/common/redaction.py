# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REDACTED = "***REDACTED***"

_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "passwd",
    "credential",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
)


def redact_headers(headers: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of HTTP headers with sensitive values redacted."""
    return {key: REDACTED if _is_sensitive_key(key) else value for key, value in headers.items()}


def redact_dict(data: Mapping[Any, Any]) -> dict[Any, Any]:
    """Recursively redact values whose dictionary keys indicate credentials."""
    return {key: REDACTED if _is_sensitive_key(key) else _redact_value(value) for key, value in data.items()}


def _is_sensitive_key(key: object) -> bool:
    normalized_key = str(key).strip().casefold().replace("-", "_")
    return any(part in normalized_key for part in _SENSITIVE_KEY_PARTS)


def _redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return redact_dict(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    return value
