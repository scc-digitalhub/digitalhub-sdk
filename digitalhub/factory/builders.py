# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
Declarative entity builders.

Most builders only say which classes an entity kind is made of. ``BuilderDef``
declares them, on top of the builder of the entity type, and generates the
builder class. ``ExecFamily`` groups an executable with the task and the run of
each of its actions, and also generates the topology that maps actions to
kinds. The generated classes have no import path: they are reached through the
registry, like every other builder.
"""

from __future__ import annotations

import re
import typing
from dataclasses import dataclass

from digitalhub.entities._mixin.runtime_entity.builder import KindAction, RuntimeEntityBuilder
from digitalhub.factory.plugins import CrudPlugin, EntityPlugin

if typing.TYPE_CHECKING:
    from collections.abc import Mapping
    from enum import Enum

    from digitalhub.entities._base.entity.builder import EntityBuilder
    from digitalhub.entities._base.entity.entity import BaseEntity
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.runtimes.builder import RuntimeBuilder


@dataclass(frozen=True)
class BuilderDef:
    """
    The classes an entity kind is made of.

    Parameters
    ----------
    kind : Enum
        Kind, for example ``EntityKinds.DATAITEM_TABLE``. Its value is the kind name.
    entity : type[BaseEntity]
        Entity class.
    spec : type[Spec]
        Spec class.
    status : type[Status]
        Status class.
    base : type[EntityBuilder]
        Builder of the entity type, for example ``DataitemBuilder``. It also
        gives the entity type.
    mixins : tuple[type, ...]
        Builder mixins placed before ``base``, for example ``SourceBuilderMixin``.
    shortcuts : tuple[CrudPlugin, ...]
        Public shortcuts of the kind, for example ``new_function_dbt``.
    """

    kind: Enum
    entity: type[BaseEntity]
    spec: type[Spec]
    status: type[Status]
    base: type[EntityBuilder]
    mixins: tuple[type, ...] = ()
    shortcuts: tuple[CrudPlugin, ...] = ()

    def plugin(self) -> EntityPlugin:
        """Generate the builder class and return the plugin that registers it."""
        return _plugin(self)


@dataclass(frozen=True)
class Action:
    """
    The task and the run of an executable action.

    Parameters
    ----------
    task : BuilderDef
        Task kind.
    run : BuilderDef
        Run kind.
    runtime_builder : type[RuntimeBuilder] | str | None
        Runtime builder of the task and the run, when it is not the one of
        the family.
    """

    task: BuilderDef
    run: BuilderDef
    runtime_builder: type[RuntimeBuilder] | str | None = None


@dataclass(frozen=True)
class ExecFamily:
    """
    An executable (function or workflow) and its actions.

    Parameters
    ----------
    executable : BuilderDef
        Executable kind.
    actions : Mapping[Enum, Action]
        Action, for example ``Actions.TRANSFORM``, to its task and run. Its
        value is the action name.
    runtime_builder : type[RuntimeBuilder] | str
        Runtime builder of the family, or its ``"package.module:Class"`` path
        (see ``EntityPlugin``). An action can declare its own.
    """

    executable: BuilderDef
    actions: Mapping[Enum, Action]
    runtime_builder: type[RuntimeBuilder] | str

    def plugins(self) -> tuple[EntityPlugin, ...]:
        """
        Generate the topology and the builders of the family.

        Every builder inherits the same topology. The plugins are the
        executable first, then the task and the run of each action.
        """
        topology = type(
            f"RuntimeEntityBuilder{_class_name(self.executable.kind.value)}",
            (RuntimeEntityBuilder,),
            {
                "__module__": __name__,
                "EXECUTABLE_KIND": self.executable.kind.value,
                "TASKS_KINDS": [
                    KindAction(action.task.kind.value, name.value) for name, action in self.actions.items()
                ],
                "RUN_KINDS": [KindAction(action.run.kind.value, name.value) for name, action in self.actions.items()],
            },
        )
        plugins = [_plugin(self.executable, (topology,), self.runtime_builder)]
        for action in self.actions.values():
            runtime_builder = action.runtime_builder or self.runtime_builder
            plugins += [
                _plugin(action.task, (topology,), runtime_builder),
                _plugin(action.run, (topology,), runtime_builder),
            ]
        return tuple(plugins)


def _plugin(
    definition: BuilderDef,
    topology: tuple[type, ...] = (),
    runtime_builder: type[RuntimeBuilder] | str | None = None,
) -> EntityPlugin:
    """Generate the builder class of a definition and return the plugin that registers it."""
    name = f"{_class_name(definition.base.ENTITY_TYPE)}{_class_name(definition.kind.value)}Builder"
    builder = type(
        name,
        (*definition.mixins, definition.base, *topology),
        {
            # Without it, ABCMeta takes the module from its own frame: 'abc'.
            "__module__": __name__,
            "ENTITY_KIND": definition.kind.value,
            "ENTITY_CLASS": definition.entity,
            "ENTITY_SPEC_CLASS": definition.spec,
            "ENTITY_STATUS_CLASS": definition.status,
        },
    )
    return EntityPlugin(
        builder=typing.cast("type[EntityBuilder]", builder),
        shortcuts=definition.shortcuts,
        runtime_builder=runtime_builder,
    )


def _class_name(text: str) -> str:
    """Turn an entity type or a kind into a class name: 'dbt+transform:run' becomes 'DbtTransformRun'."""
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[^0-9A-Za-z]+", text) if part)
