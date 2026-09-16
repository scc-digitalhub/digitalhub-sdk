# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class BaseCollectionTarget:
    entity_type: str


@dataclass(frozen=True, slots=True)
class BaseEntityTarget:
    entity_type: str
    entity_name: str


@dataclass(frozen=True, slots=True)
class ContextProjectTarget:
    project: str


@dataclass(frozen=True, slots=True)
class ContextCollectionTarget:
    project: str
    entity_type: str


@dataclass(frozen=True, slots=True)
class ContextEntityTarget:
    project: str
    entity_type: str
    entity_id: str


@dataclass(frozen=True, slots=True)
class ContextMetricTarget:
    project: str
    entity_type: str
    entity_id: str
    metric_name: str | None


RouteTarget: TypeAlias = (
    BaseCollectionTarget
    | BaseEntityTarget
    | ContextProjectTarget
    | ContextCollectionTarget
    | ContextEntityTarget
    | ContextMetricTarget
)
