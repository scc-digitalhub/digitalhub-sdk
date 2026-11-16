# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, TypeVar

from digitalhub.factory.enums import FactoryEnum
from digitalhub.factory.plugins import CrudPlugin, EntityPlugin
from digitalhub.factory.utils import import_module, list_runtimes
from digitalhub.utils.exceptions import BuilderError

if TYPE_CHECKING:
    from digitalhub.entities._base.entity.builder import EntityBuilder
    from digitalhub.entities._mixin.runtime_entity.builder import RuntimeEntityBuilder
    from digitalhub.runtimes.builder import RuntimeBuilder

BuilderT = TypeVar("BuilderT")


class BuilderRegistry:
    """
    Registry for resolving entity, runtime, and CRUD plugins.

    Registrations are loaded lazily from the core SDK and installed runtime modules.
    """

    def __init__(self) -> None:
        self._entity_builders: dict[str, EntityBuilder | RuntimeEntityBuilder] = {}
        self._generic_entity_builders: dict[str, EntityBuilder | RuntimeEntityBuilder] = {}
        self._runtime_builders: dict[str, RuntimeBuilder] = {}
        self._crud_plugins: dict[str, CrudPlugin] = {}
        self._entities_registered = False
        self._runtimes_registered = False

    @staticmethod
    def _add_builder(
        registry: dict[str, BuilderT],
        name: str,
        builder: type[BuilderT],
        duplicate_error: str,
    ) -> None:
        if name in registry:
            raise BuilderError(duplicate_error)
        registry[name] = builder()

    def get_entity_builder(
        self,
        kind: str,
        entity_type: str | None = None,
    ) -> EntityBuilder | RuntimeEntityBuilder:
        """
        Retrieve the entity builder for the given kind, ensuring lazy registration.

        Parameters
        ----------
        kind : str
            The kind of entity builder to retrieve.

        Returns
        -------
        EntityBuilder | RuntimeEntityBuilder
            The builder instance.
        """
        if not self._entities_registered:
            self._ensure_entities_registered()
        if kind not in self._entity_builders and not self._runtimes_registered:
            self._ensure_runtimes_registered()
        if kind in self._entity_builders:
            return self._entity_builders[kind]
        if entity_type is not None and entity_type in self._generic_entity_builders:
            return self._generic_entity_builders[entity_type]
        raise BuilderError(f"Entity builder for kind '{kind}' not found.")

    def get_runtime_builder(self, kind: str) -> RuntimeBuilder:
        """
        Retrieve the runtime builder for the given kind, ensuring lazy registration.

        Parameters
        ----------
        kind : str
            The kind of runtime builder to retrieve.

        Returns
        -------
        RuntimeBuilder
            The builder instance.
        """
        if kind not in self._runtime_builders and not self._runtimes_registered:
            self._ensure_runtimes_registered()
        try:
            return self._runtime_builders[kind]
        except KeyError as e:
            raise BuilderError(f"Runtime builder for kind '{kind}' not found.") from e

    def get_shortcut(self, name: str) -> Callable[..., Any]:
        """Retrieve a registered shortcut."""
        return self.get_shortcut_spec(name).function

    def get_shortcut_spec(self, name: str) -> CrudPlugin:
        """Retrieve the declaration for a registered shortcut."""
        self._ensure_shortcut_registered(name)
        try:
            return self._crud_plugins[name]
        except KeyError as e:
            raise AttributeError(f"Shortcut '{name}' not found.") from e

    def _ensure_shortcut_registered(self, name: str) -> None:
        if not self._entities_registered:
            self._ensure_entities_registered()
        if name not in self._crud_plugins and not self._runtimes_registered:
            self._ensure_runtimes_registered()

    def get_shortcut_names(self) -> tuple[str, ...]:
        """Return registered shortcut names in deterministic order."""
        if not self._entities_registered:
            self._ensure_entities_registered()
        if not self._runtimes_registered:
            self._ensure_runtimes_registered()
        return tuple(sorted(self._crud_plugins))

    def get_project_shortcut_names(self) -> tuple[str, ...]:
        """Return registered shortcuts that can be bound to a project."""
        self.get_shortcut_names()
        return tuple(name for name, spec in sorted(self._crud_plugins.items()) if spec.project_bound)

    def _ensure_entities_registered(self) -> None:
        """
        Ensure core entities are registered on-demand.
        """
        if self._entities_registered:
            return
        try:
            self._register_entities()
            self._entities_registered = True
        except Exception as e:
            raise BuilderError(f"Failed to register core entities: {e}") from e

    def _register_entities(self) -> None:
        """
        Register core entity builders into the registry.
        """
        module = import_module(FactoryEnum.REG_ENTITIES.value)
        entity_builders = self._entity_builders.copy()
        generic_entity_builders = self._generic_entity_builders.copy()
        runtime_builders = self._runtime_builders.copy()
        crud_plugins = self._crud_plugins.copy()

        entity_plugins = getattr(module, FactoryEnum.REG_ENTITY_PLUGINS_VAR.value, ())
        self._register_entity_plugins(entity_plugins, entity_builders, crud_plugins, runtime_builders)
        self._register_crud_plugins(
            getattr(module, FactoryEnum.REG_CRUD_PLUGINS_VAR.value, ()),
            crud_plugins,
        )

        if not entity_plugins:
            for name, builder in getattr(module, FactoryEnum.REG_ENTITIES_VAR.value, []):
                self._add_builder(entity_builders, name, builder, f"Builder {name} already exists.")

        for entity_type, builder in getattr(module, FactoryEnum.REG_GENERIC_ENTITIES_VAR.value, []):
            self._add_builder(
                generic_entity_builders,
                entity_type,
                builder,
                f"Generic builder for {entity_type} already exists.",
            )

        self._entity_builders = entity_builders
        self._generic_entity_builders = generic_entity_builders
        self._runtime_builders = runtime_builders
        self._crud_plugins = crud_plugins

    def _ensure_runtimes_registered(self) -> None:
        """
        Ensure runtime entities are registered on-demand.
        """
        if self._runtimes_registered:
            return
        try:
            self._register_runtimes_entities()
            self._runtimes_registered = True
        except BuilderError:
            raise
        except Exception as e:
            raise BuilderError(f"Failed to register runtime entities: {e}") from e

    def _register_runtimes_entities(self) -> None:
        """
        Register runtime plugins, including their entity and runtime builders.
        """
        entity_builders = self._entity_builders.copy()
        runtime_builders = self._runtime_builders.copy()
        crud_plugins = self._crud_plugins.copy()

        for package in sorted(list_runtimes()):
            module = import_module(package)
            entity_plugins = getattr(module, FactoryEnum.REG_ENTITY_PLUGINS_VAR.value, None)
            if entity_plugins is None:
                raise BuilderError(f"Runtime package '{package}' does not define 'entity_plugins'.")
            self._register_entity_plugins(entity_plugins, entity_builders, crud_plugins, runtime_builders)

        self._entity_builders = entity_builders
        self._runtime_builders = runtime_builders
        self._crud_plugins = crud_plugins

    def _register_entity_plugins(
        self,
        entity_plugins: Iterable[EntityPlugin],
        entity_builders: dict[str, EntityBuilder | RuntimeEntityBuilder],
        crud_plugins: dict[str, CrudPlugin],
        runtime_builders: dict[str, RuntimeBuilder],
    ) -> None:
        for plugin in entity_plugins:
            self._add_builder(
                entity_builders,
                plugin.kind,
                plugin.builder,
                f"Builder {plugin.kind} already exists.",
            )
            if plugin.runtime_builder is not None:
                self._add_builder(
                    runtime_builders,
                    plugin.kind,
                    plugin.runtime_builder,
                    f"Runtime builder for {plugin.kind} already exists.",
                )
            for crud_plugin in plugin.shortcuts:
                self._add_crud_plugins(crud_plugins, crud_plugin)

    def _register_crud_plugins(
        self,
        crud_plugins: Iterable[CrudPlugin],
        crud_plugins_dict: dict[str, CrudPlugin],
    ) -> None:
        for crud_plugin in crud_plugins:
            self._add_crud_plugins(crud_plugins_dict, crud_plugin)

    @staticmethod
    def _add_crud_plugins(crud_plugins_dict: dict[str, CrudPlugin], crud_plugin: CrudPlugin) -> None:
        if crud_plugin.name in crud_plugins_dict:
            raise BuilderError(f"Shortcut {crud_plugin.name} already exists.")
        crud_plugins_dict[crud_plugin.name] = crud_plugin


# Global singleton instance
registry = BuilderRegistry()
