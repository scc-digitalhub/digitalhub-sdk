# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.common.enums import OpsType


@dataclass(frozen=True, slots=True)
class BERequest:
    """Immutable description of one request sent to DigitalHub Core."""

    method: str
    api: str
    operation: str | OpsType = OpsType.HTTP_REQUEST
    params: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    data: Any = None
    timeout: float | tuple[float, float] | None = field(default_factory=lambda: get_client_config().http_timeout)
    authenticate: bool = True
    options: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_http(
        cls,
        method: str,
        api: str,
        *,
        operation: str | OpsType = OpsType.HTTP_REQUEST,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> BERequest:
        request_options = dict(kwargs)
        return cls(
            method=method,
            api=api,
            operation=operation,
            params=request_options.pop("params", {}),
            headers=request_options.pop("headers", {}),
            data=request_options.pop("data", None),
            timeout=request_options.pop("timeout", get_client_config().http_timeout),
            authenticate=authenticate,
            options=request_options,
        )

    @classmethod
    def get(
        cls,
        api: str,
        *,
        operation: str | OpsType = OpsType.HTTP_REQUEST,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> BERequest:
        return cls.from_http(
            "GET",
            api,
            operation=operation,
            authenticate=authenticate,
            **kwargs,
        )

    @classmethod
    def post(
        cls,
        api: str,
        *,
        operation: str | OpsType = OpsType.HTTP_REQUEST,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> BERequest:
        return cls.from_http(
            "POST",
            api,
            operation=operation,
            authenticate=authenticate,
            **kwargs,
        )

    @classmethod
    def put(
        cls,
        api: str,
        *,
        operation: str | OpsType = OpsType.HTTP_REQUEST,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> BERequest:
        return cls.from_http(
            "PUT",
            api,
            operation=operation,
            authenticate=authenticate,
            **kwargs,
        )

    @classmethod
    def delete(
        cls,
        api: str,
        *,
        operation: str | OpsType = OpsType.HTTP_REQUEST,
        authenticate: bool = True,
        **kwargs: Any,
    ) -> BERequest:
        return cls.from_http(
            "DELETE",
            api,
            operation=operation,
            authenticate=authenticate,
            **kwargs,
        )

    def __post_init__(self) -> None:
        if isinstance(self.operation, OpsType):
            object.__setattr__(self, "operation", self.operation.value)
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))
        object.__setattr__(self, "options", MappingProxyType(dict(self.options)))

    def to_transport_kwargs(self) -> dict[str, Any]:
        """Convert structured fields to arguments accepted by the transport."""
        transport_kwargs: dict[str, Any] = dict(self.options)
        if self.params:
            transport_kwargs["params"] = dict(self.params)
        if self.headers:
            transport_kwargs["headers"] = dict(self.headers)
        if self.data is not None:
            transport_kwargs["data"] = self.data
        if self.timeout is not None:
            transport_kwargs["timeout"] = self.timeout
        return transport_kwargs
