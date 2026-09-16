# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.options import NoOptions, OperationOptions
from digitalhub.stores.client.compiler.targets import RouteTarget


@dataclass(frozen=True, slots=True)
class ClientOp:
    """Immutable semantic request for a DigitalHub backend operation."""

    category: ApiType
    operation: BackendOp
    target: RouteTarget
    options: OperationOptions = field(default_factory=NoOptions)
    payload: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", ApiType(self.category))
        object.__setattr__(self, "operation", BackendOp(self.operation))
