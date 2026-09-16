# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

_MISSING = object()


@dataclass(frozen=True, slots=True)
class ParameterState:
    """Immutable intermediate state for request parameter construction."""

    values: Mapping[str, Any] = field(default_factory=dict)
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))

    @classmethod
    def from_kwargs(cls, kwargs: Mapping[str, Any]) -> ParameterState:
        values = dict(kwargs)
        params = values.pop("params", {})
        return cls(values=values, params=params)

    def pop(self, key: str, default: Any = _MISSING) -> tuple[Any, ParameterState]:
        values = dict(self.values)
        if default is _MISSING:
            value = values.pop(key)
        else:
            value = values.pop(key, default)
        return value, replace(self, values=values)

    def with_value(self, key: str, value: Any) -> ParameterState:
        values = {**self.values, key: value}
        return replace(self, values=values)

    def with_param(self, key: str, value: Any) -> ParameterState:
        params = {**self.params, key: value}
        return replace(self, params=params)

    def to_kwargs(self) -> dict[str, Any]:
        if self.values:
            unsupported = ", ".join(sorted(self.values))
            raise ValueError(f"Unsupported backend parameters: {unsupported}.")
        return {"params": dict(self.params)}
