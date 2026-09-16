# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, TypeAlias


@dataclass(frozen=True, slots=True)
class NoOptions:
    def to_values(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True, slots=True)
class ReadOptions:
    name: str | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class ReadAllVersionsOptions:
    name: str

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class ListOptions:
    q: str | None = None
    name: str | None = None
    kind: str | None = None
    user: str | None = None
    state: str | None = None
    created: str | None = None
    updated: str | None = None
    versions: str | None = None
    function: str | None = None
    workflow: str | None = None
    action: str | None = None
    task: str | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class DeleteOptions:
    cascade: bool | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class DeleteAllVersionsOptions:
    name: str
    cascade: bool | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class SearchOptions:
    query: str | None = None
    entity_types: list[str] | None = None
    name: str | None = None
    kind: str | None = None
    state: str | None = None
    created: str | None = None
    updated: str | None = None
    description: str | None = None
    labels: list[str] | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class ShareOptions:
    user: str
    unshare: bool = False
    share_id: str | None = None
    role: str | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class LogsOptions:
    state: str | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class MetricsOptions:
    user: str | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class StopResumeOptions:
    reason: str | None = None

    def to_values(self) -> dict[str, Any]:
        return _dataclass_values(self)


@dataclass(frozen=True, slots=True)
class OpaqueOptions:
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def to_values(self) -> dict[str, Any]:
        return dict(self.values)


OperationOptions: TypeAlias = (
    NoOptions
    | ReadOptions
    | ReadAllVersionsOptions
    | ListOptions
    | DeleteOptions
    | DeleteAllVersionsOptions
    | SearchOptions
    | ShareOptions
    | LogsOptions
    | MetricsOptions
    | StopResumeOptions
    | OpaqueOptions
)


def _dataclass_values(options: Any) -> dict[str, Any]:
    return {
        item.name: getattr(options, item.name) for item in fields(options) if getattr(options, item.name) is not None
    }
