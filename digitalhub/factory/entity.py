# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Literal, overload

from digitalhub.factory.enums import BuilderMethodsEnum
from digitalhub.factory.registry import registry
from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.entity.spec import Spec, SpecValidator
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities._mixin.executable.protocol import ExecutableEntityProtocol
    from digitalhub.entities._mixin.material.protocol import MaterialEntityProtocol
    from digitalhub.entities._mixin.metrics.protocol import MetricsEntityProtocol
    from digitalhub.entities._mixin.unversioned.protocol import UnversionedEntityProtocol
    from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol


class EntityFactory:
    """
    Factory for creating and managing entity builders.
    """

    def _call_builder_method(self, kind: str, method_name: str, *args, **kwargs):
        """
        Helper method to get a builder and call a method on it.

        Parameters
        ----------
        kind : str
            The kind of builder to retrieve.
        method_name : str
            The name of the method to call on the builder.
        *args
            Positional arguments to pass to the method.
        **kwargs
            Keyword arguments to pass to the method.

        Returns
        -------
        Any
            The result of calling the method on the builder.
        """
        builder = registry.get_entity_builder(kind)
        return getattr(builder, method_name)(*args, **kwargs)

    @overload
    def build_entity_from_params(
        self, entity_type: Literal["artifact", "dataitem", "model"], **kwargs
    ) -> MaterialEntityProtocol: ...

    @overload
    def build_entity_from_params(
        self, entity_type: Literal["function", "workflow"], **kwargs
    ) -> ExecutableEntityProtocol: ...

    @overload
    def build_entity_from_params(self, entity_type: Literal["run"], **kwargs) -> MetricsEntityProtocol: ...

    @overload
    def build_entity_from_params(self, entity_type: Literal["task"], **kwargs) -> UnversionedEntityProtocol: ...

    @overload
    def build_entity_from_params(
        self, entity_type: Literal["containerimage", "log", "secret", "trigger"], **kwargs
    ) -> VersionedEntityProtocol: ...

    @overload
    def build_entity_from_params(self, entity_type: str | None = None, **kwargs) -> ContextEntity: ...

    def build_entity_from_params(self, entity_type: str | None = None, **kwargs) -> ContextEntity:
        """
        Build an entity from parameters.

        Parameters
        ----------
        **kwargs
            Entity parameters.

        Returns
        -------
        Entity
            Entity object.
        """
        kind = self._get_kind(**kwargs)
        builder = registry.get_entity_builder(kind, entity_type=entity_type)
        return builder.build(**kwargs)

    @overload
    def build_entity_from_dict(
        self, obj: dict, entity_type: Literal["artifact", "dataitem", "model"]
    ) -> MaterialEntityProtocol: ...

    @overload
    def build_entity_from_dict(
        self, obj: dict, entity_type: Literal["function", "workflow"]
    ) -> ExecutableEntityProtocol: ...

    @overload
    def build_entity_from_dict(self, obj: dict, entity_type: Literal["run"]) -> MetricsEntityProtocol: ...

    @overload
    def build_entity_from_dict(self, obj: dict, entity_type: Literal["task"]) -> UnversionedEntityProtocol: ...

    @overload
    def build_entity_from_dict(
        self, obj: dict, entity_type: Literal["containerimage", "log", "secret", "trigger"]
    ) -> VersionedEntityProtocol: ...

    @overload
    def build_entity_from_dict(self, obj: dict, entity_type: str | None = None) -> ContextEntity: ...

    def build_entity_from_dict(self, obj: dict, entity_type: str | None = None) -> ContextEntity:
        """
        Build an entity from a dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary with entity data.

        Returns
        -------
        Entity
            Entity object.
        """
        kind = self._get_kind(**obj)
        builder = registry.get_entity_builder(kind, entity_type=entity_type)
        return builder.from_dict(obj)

    def build_spec(self, kind_to_build_from: str, **kwargs) -> Spec:
        """
        Build an entity spec.

        Parameters
        ----------
        kind_to_build_from : str
            Entity type.
        **kwargs
            Additional spec parameters.

        Returns
        -------
        Spec
            Spec object.
        """
        return self._call_builder_method(kind_to_build_from, BuilderMethodsEnum.BUILD_SPEC.value, **kwargs)

    def build_metadata(self, kind_to_build_from: str, **kwargs) -> Metadata:
        """
        Build an entity metadata.

        Parameters
        ----------
        kind_to_build_from : str
            Entity type.
        **kwargs
            Additional metadata parameters.

        Returns
        -------
        Metadata
            Metadata object.
        """
        return self._call_builder_method(kind_to_build_from, BuilderMethodsEnum.BUILD_METADATA.value, **kwargs)

    def build_status(self, kind_to_build_from: str, **kwargs) -> Status:
        """
        Build an entity status.

        Parameters
        ----------
        kind_to_build_from : str
            Entity type.
        **kwargs
            Additional status parameters.

        Returns
        -------
        Status
            Status object.
        """
        return self._call_builder_method(
            kind_to_build_from,
            BuilderMethodsEnum.BUILD_STATUS.value,
            **kwargs,
        )

    def get_entity_type_from_kind(self, kind: str) -> str:
        """
        Get entity type from builder.

        Parameters
        ----------
        kind : str
            Entity type.

        Returns
        -------
        str
            Entity type.
        """
        return self._call_builder_method(kind, BuilderMethodsEnum.GET_ENTITY_TYPE.value)

    def get_executable_kind(self, kind: str) -> str:
        """
        Get executable kind.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        str
            Executable kind.
        """
        return self._call_builder_method(kind, BuilderMethodsEnum.GET_EXECUTABLE_KIND.value)

    def get_action_from_task_kind(self, kind: str, task_kind: str) -> str:
        """
        Get action from task.

        Parameters
        ----------
        kind : str
            Kind.
        task_kind : str
            Task kind.

        Returns
        -------
        str
            Action.
        """
        return self._call_builder_method(
            kind,
            BuilderMethodsEnum.GET_ACTION_FROM_TASK_KIND.value,
            task_kind,
        )

    def get_task_kind_from_action(self, kind: str, action: str) -> str:
        """
        Get task kind from action.

        Parameters
        ----------
        kind : str
            Kind.
        action : str
            Action.

        Returns
        -------
        str
            Task kind.
        """
        return self._call_builder_method(
            kind,
            BuilderMethodsEnum.GET_TASK_KIND_FROM_ACTION.value,
            action,
        )

    def get_run_kind_from_action(self, kind: str, action: str) -> str:
        """
        Get run kind.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        str
            Run kind.
        """
        return self._call_builder_method(
            kind,
            BuilderMethodsEnum.GET_RUN_KIND_FROM_ACTION.value,
            action,
        )

    def get_all_kinds(self, kind: str) -> list[str]:
        """
        Get all kinds.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        list of str
            All kinds.
        """
        return self._call_builder_method(kind, BuilderMethodsEnum.GET_ALL_KINDS.value)

    def get_spec_validator(self, kind: str) -> SpecValidator:
        """
        Get spec validators.

        Parameters
        ----------
        kind : str
            Kind.

        Returns
        -------
        SpecValidator
            Spec validator.
        """
        return self._call_builder_method(kind, BuilderMethodsEnum.GET_SPEC_VALIDATOR.value)

    @staticmethod
    def _get_kind(**kwargs) -> str:
        """
        Extract the 'kind' from parameters.

        Parameters
        ----------
        **kwargs
            Entity parameters.

        Returns
        -------
        str
            The kind of the entity.
        """
        try:
            return kwargs["kind"]
        except KeyError:
            raise BuilderError("Missing 'kind' parameter.")


# Global instance
entity_factory = EntityFactory()
