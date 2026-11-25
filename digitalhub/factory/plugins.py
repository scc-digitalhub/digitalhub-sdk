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
    from digitalhub.runtimes.builder import RuntimeBuilder


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
    """
    Registration bundle for an entity kind and its optional runtime support.

    ``runtime_builder`` is either the class or its ``"package.module:Class"``
    path. Use the path when the runtime imports execution dependencies that may
    be missing: the entity still registers, and the import error is reported,
    with its cause, when the runtime is first used.
    """

    builder: type[EntityBuilder]
    shortcuts: tuple[CrudPlugin, ...] = ()
    runtime_builder: type[RuntimeBuilder] | str | None = None

    @property
    def kind(self) -> str:
        """Return the entity kind declared by the builder."""
        return self.builder.ENTITY_KIND
