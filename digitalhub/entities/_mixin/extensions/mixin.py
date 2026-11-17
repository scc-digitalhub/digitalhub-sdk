# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar


class ExtensionsMixin:
    """Provide top-level extensions for serializable entities."""

    _obj_attr: ClassVar[tuple[str, ...]] = ("extensions",)
    extensions: list[dict]

    def _init_extensions(self, extensions: list[dict] | None = None) -> None:
        self.extensions = extensions if extensions is not None else []
