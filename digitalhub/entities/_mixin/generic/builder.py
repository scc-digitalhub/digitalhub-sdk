# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus


class GenericBuilder:
    """Mixin that builds a pass-through generic spec."""

    def build_spec(self, **kwargs) -> GenericSpec:
        return GenericSpec(**kwargs)

    def build_status(self, **kwargs) -> GenericStatus:
        return GenericStatus(**kwargs)
