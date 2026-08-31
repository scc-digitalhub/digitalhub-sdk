# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.factory.enums import FactoryEnum
from digitalhub.factory.utils import import_module, list_runtimes
from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.builder import EntityBuilder
    from digitalhub.entities._mixin.runtime_entity.builder import RuntimeEntityBuilder
    from digitalhub.runtimes.builder import RuntimeBuilder

BuilderT = typing.TypeVar("BuilderT")


class BuilderRegistry:
    """
    Singleton registry for managing imported modules and builders.

    This class centralizes the registration and retrieval of entity and runtime builders,
    ensuring lazy loading and a single source of truth for available builders.
    """

    def __init__(self) -> None:
        self._instance: BuilderRegistry | None = None
        self._initialized = False
        self._entity_builders: dict[str, EntityBuilder | RuntimeEntityBuilder] = {}
        self._generic_entity_builders: dict[str, EntityBuilder | RuntimeEntityBuilder] = {}
        self._runtime_builders: dict[str, RuntimeBuilder] = {}
        self._entities_registered = False
        self._runtimes_registered = False

    def add_entity_builder(
        self,
        name: str,
        builder: type[EntityBuilder | RuntimeEntityBuilder],
    ) -> None:
        """
        Register an entity builder.

        Parameters
        ----------
        name : str
            The unique identifier for the builder.
        builder : type[EntityBuilder] | type[RuntimeEntityBuilder]
            The builder class to register. It will be instantiated immediately.
        """
        self._add_builder(self._entity_builders, name, builder, f"Builder {name} already exists.")

    def add_runtime_builder(self, name: str, builder: type[RuntimeBuilder]) -> None:
        """
        Register a runtime builder.

        Parameters
        ----------
        name : str
            The unique identifier for the builder.
        builder : type[RuntimeBuilder]
            The builder class to register. It will be instantiated immediately.
        """
        self._add_builder(self._runtime_builders, name, builder, f"Builder {name} already exists.")

    def add_generic_entity_builder(
        self,
        entity_type: str,
        builder: type[EntityBuilder | RuntimeEntityBuilder],
    ) -> None:
        """
        Register a generic entity builder for a given entity type.

        Parameters
        ----------
        entity_type : str
            The entity type used as fallback key.
        builder : type[EntityBuilder] | type[RuntimeEntityBuilder]
            The builder class to register. It will be instantiated immediately.
        """
        self._add_builder(
            self._generic_entity_builders,
            entity_type,
            builder,
            f"Generic builder for {entity_type} already exists.",
        )

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
        if kind not in self._entity_builders:
            if not self._runtimes_registered:
                self._ensure_runtimes_registered()
            if kind not in self._entity_builders:
                if entity_type is not None and entity_type in self._generic_entity_builders:
                    return self._generic_entity_builders[entity_type]
                raise BuilderError(f"Entity builder for kind '{kind}' not found.")
        return self._entity_builders[kind]

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
        if kind not in self._runtime_builders:
            if not self._runtimes_registered:
                self._ensure_runtimes_registered()
            if kind not in self._runtime_builders:
                raise BuilderError(f"Runtime builder for kind '{kind}' not found.")
        return self._runtime_builders[kind]

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
        try:
            module = import_module(FactoryEnum.REG_ENTITIES.value)
            entity_builders = self._entity_builders.copy()
            generic_entity_builders = self._generic_entity_builders.copy()

            # Register core entities
            for k, b in getattr(module, FactoryEnum.REG_ENTITIES_VAR.value, []):
                self._add_builder(entity_builders, k, b, f"Builder {k} already exists.")

            # Register generic fallback entities
            for k, b in getattr(module, FactoryEnum.REG_GENERIC_ENTITIES_VAR.value, []):
                self._add_builder(
                    generic_entity_builders,
                    k,
                    b,
                    f"Generic builder for {k} already exists.",
                )

            self._entity_builders, self._generic_entity_builders = entity_builders, generic_entity_builders

        except Exception as e:
            raise RuntimeError("Error registering core entities.") from e

    def _ensure_runtimes_registered(self) -> None:
        """
        Ensure runtime entities are registered on-demand.
        """
        if self._runtimes_registered:
            return
        try:
            self._register_runtimes_entities()
            self._runtimes_registered = True
        except Exception as e:
            raise BuilderError(f"Failed to register runtime entities: {e}") from e

    def _register_runtimes_entities(self) -> None:
        """
        Register all runtime builders and their entities into the registry.
        """
        try:
            entity_builders = self._entity_builders.copy()
            runtime_builders = self._runtime_builders.copy()

            for package in list_runtimes():
                module = import_module(package)

                # Register workflows, functions, tasks and runs entities builders
                for k, b in getattr(module, FactoryEnum.REG_ENTITIES_VAR.value, []):
                    self._add_builder(entity_builders, k, b, f"Builder {k} already exists.")

                # Register runtime builders
                for k, b in getattr(module, FactoryEnum.REG_RUNTIME_VAR.value, []):
                    self._add_builder(runtime_builders, k, b, f"Builder {k} already exists.")

            self._entity_builders, self._runtime_builders = entity_builders, runtime_builders
        except Exception as e:
            raise RuntimeError("Error registering runtime entities.") from e


# Global singleton instance
registry = BuilderRegistry()
