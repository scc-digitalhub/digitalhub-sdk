# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from digitalhub.stores.client.common.enums import ApiType, BEOps


@dataclass(frozen=True, slots=True)
class ClientOp:
    """Immutable semantic request for a DigitalHub backend operation."""

    category: ApiType
    operation: BEOps
    route_args: Mapping[str, Any] = field(default_factory=dict)
    params: Mapping[str, Any] = field(default_factory=dict)
    payload: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", ApiType(self.category))
        object.__setattr__(self, "operation", BEOps(self.operation))
        object.__setattr__(self, "route_args", MappingProxyType(dict(self.route_args)))
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))
