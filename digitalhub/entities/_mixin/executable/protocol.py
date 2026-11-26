# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Protocol

from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol


class ExecutableProtocol(VersionedEntityProtocol, Protocol):
    """What processors need from a function or workflow; the user methods are defined by the executable mixins."""

    def _get_executable_string(self) -> str: ...
