# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.builder import EntityBuilder


@dataclass(frozen=True)
class CrudPlugin:
    """Declaration for a public shortcut."""

    function: Callable[..., Any]
    project_bound: bool = True
    refresh_project: bool = True
    validate_entity_project: bool = False
    inject_context: bool = False

    @property
    def name(self) -> str:
        """Return the public name of the shortcut function."""
        return self.function.__name__


@dataclass(frozen=True)
class EntityPlugin:
    """Entity builder and public extensions owned by one plugin."""

    builder: EntityBuilder
    shortcuts: tuple[CrudPlugin, ...] = ()

    @property
    def kind(self) -> str:
        """Return the entity kind declared by the builder."""
        return self.builder.ENTITY_KIND
