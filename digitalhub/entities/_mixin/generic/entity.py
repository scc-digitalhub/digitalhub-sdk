# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class GenericMixin:
    """Mixin for entities that need to keep arbitrary runtime fields."""

    def _set_generic_attributes(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if k not in self.__dict__:
                setattr(self, k, v)
