# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol

from digitalhub.entities._mixin.source.models import SourceCode
from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context


class SourceSpecProtocol(Protocol):
    source: SourceCode | None


class SourceEntityProtocol(VersionedEntityProtocol, Protocol):
    spec: SourceSpecProtocol

    def _context(self) -> Context: ...
