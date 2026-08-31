# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Protocol


class _SupportsRunExtensions(Protocol):
    extensions: list[dict]


def init_run_extensions(entity: _SupportsRunExtensions, extensions: list[dict] | None = None) -> None:
    entity.extensions = extensions if extensions is not None else []
