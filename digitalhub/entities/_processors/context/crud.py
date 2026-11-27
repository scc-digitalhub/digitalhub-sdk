# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any, Protocol, TypeVar

from digitalhub.entities._commons.keys import EntityKey, is_valid_key
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.utils import (
    get_context,
    get_context_from_identifier,
    parse_identifier,
    update_entity_identity,
)
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import (
    DeleteAllVersionsOptions,
    DeleteOptions,
    ListOptions,
    ReadAllVersionsOptions,
    ReadOptions,
)
from digitalhub.stores.client.compiler.targets import ContextCollectionTarget, ContextEntityTarget
from digitalhub.utils.exceptions import BuilderError, EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml, write_yaml

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._mixin.unversioned.protocol import UnversionedEntityProtocol


class _StoredEntity(Protocol):
    """What the processor needs to save an entity and update it with the stored state."""

    # Read-only members: entity classes and the entity protocols both match.
    @property
    def ENTITY_TYPE(self) -> str: ...

    @property
    def project(self) -> str: ...

    @property
    def id(self) -> str: ...

    @property
    def key(self) -> str: ...

    def to_dict(self) -> dict: ...

    def _update_attributes(self, obj: Any) -> None: ...


StoredEntityT = TypeVar("StoredEntityT", bound=_StoredEntity)


class ContextEntityCRUDProcessor:
    def create_context_entity(self, obj: StoredEntityT) -> StoredEntityT:
        """Create ``obj`` in the backend and update it with the stored state."""
        context = get_context(obj.project)
        stored = context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.CREATE,
                target=ContextCollectionTarget(context.name, obj.ENTITY_TYPE),
                payload=obj.to_dict(),
            )
        )
        obj._update_attributes(entity_factory.build_entity_from_dict(stored, entity_type=obj.ENTITY_TYPE))
        return obj

    def create_context_entity_from_params(self, entity_type: str, **kwargs) -> ContextEntity:
        """Build an entity of ``entity_type`` from parameters, then create it."""
        entity_kind = kwargs.get("kind")
        try:
            expected_type = entity_factory.get_entity_type_from_kind(entity_kind)
        except BuilderError:
            expected_type = entity_type
        if entity_type != expected_type:
            raise ValueError(
                f"Entity kind '{entity_kind}' does not match expected type '{expected_type}'.",
            )
        obj: ContextEntity = entity_factory.build_entity_from_params(entity_type=entity_type, **kwargs)
        obj._post_create_hook_before_save()
        return self.create_context_entity(obj)

    def export_context_entity(self, _entity: ContextEntity) -> str:
        obj = _entity.to_dict()
        context = _entity._context()
        pth = context.ensure_root() / f"{_entity.ENTITY_TYPE}s-{_entity.id}.yaml"
        write_yaml(pth, obj)
        return str(pth)

    def read_context_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> ContextEntity:
        context = get_context_from_identifier(identifier, project)
        # The type comes from the key when only the key is given, so that
        # kinds of runtimes that are not installed still read as generic.
        _, entity_type, _, entity_name, entity_id = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if entity_id is None:
            kwargs["name"] = entity_name
            obj = context.client.execute_first(
                ClientOp(
                    category=ApiType.CONTEXT,
                    operation=BackendOp.LIST,
                    target=ContextCollectionTarget(context.name, entity_type),
                    options=ListOptions(**kwargs),
                )
            )
        else:
            obj = context.client.execute(
                ClientOp(
                    category=ApiType.CONTEXT,
                    operation=BackendOp.READ,
                    target=ContextEntityTarget(context.name, entity_type, entity_id),
                    options=ReadOptions(**kwargs),
                )
            )
        return entity_factory.build_entity_from_dict(obj, entity_type=entity_type)

    def read_unversioned_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> UnversionedEntityProtocol:
        if not is_valid_key(identifier):
            entity_id = identifier
        return self.read_context_entity(
            identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )

    def read_context_entity_versions(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        **kwargs,
    ) -> list[ContextEntity]:
        context = get_context_from_identifier(identifier, project)
        _, entity_type, _, entity_name, _ = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
        )
        objs = context.client.execute_list(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.READ_ALL_VERSIONS,
                target=ContextCollectionTarget(context.name, entity_type),
                options=ReadAllVersionsOptions(name=entity_name),
            )
        )
        objects = []
        for o in objs:
            entity_type = EntityKey.parse(o["key"]).entity_type
            entity: ContextEntity = entity_factory.build_entity_from_dict(o, entity_type=entity_type)
            objects.append(entity)
        return objects

    def import_context_entity(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ContextEntity:
        if (file is None) == (key is None):
            raise ValueError("Provide key or file, not both or none.")

        if file is not None:
            dict_obj: dict = read_yaml(file)
        else:
            dict_obj = self.read_context_entity(key).to_dict()

        dict_obj["status"] = {}

        if context is None:
            context = dict_obj["project"]

        entity_type = EntityKey.parse(dict_obj["key"]).entity_type

        obj = entity_factory.build_entity_from_dict(dict_obj, entity_type=entity_type)
        update_entity_identity(obj, context, build_uuid() if reset_id else None)
        try:
            return self.create_context_entity(obj)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")

    def load_context_entity(
        self,
        file: str,
    ) -> ContextEntity:
        dict_obj: dict = read_yaml(file)
        entity_type = EntityKey.parse(dict_obj["key"]).entity_type
        obj: ContextEntity = entity_factory.build_entity_from_dict(dict_obj, entity_type=entity_type)
        try:
            return self.update_context_entity(obj)
        except EntityNotExistsError:
            return self.create_context_entity(obj)

    def list_context_entities(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> list[ContextEntity]:
        context = get_context(project)
        objs = context.client.execute_list(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.LIST,
                target=ContextCollectionTarget(context.name, entity_type),
                options=ListOptions(**kwargs),
            )
        )
        objects = []
        for o in objs:
            entity: ContextEntity = entity_factory.build_entity_from_dict(o, entity_type=entity_type)
            objects.append(entity)
        return objects

    def update_context_entity(self, obj: StoredEntityT) -> StoredEntityT:
        """Update ``obj`` in the backend and update it with the stored state."""
        context = get_context(obj.project)
        stored = context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.UPDATE,
                target=ContextEntityTarget(context.name, obj.ENTITY_TYPE, obj.id),
                payload=obj.to_dict(),
            )
        )
        obj._update_attributes(entity_factory.build_entity_from_dict(stored, entity_type=obj.ENTITY_TYPE))
        return obj

    def refresh_context_entity(self, obj: StoredEntityT) -> StoredEntityT:
        """Update ``obj`` with the stored state."""
        obj._update_attributes(self.read_context_entity(obj.key, entity_type=obj.ENTITY_TYPE))
        return obj

    def delete_context_entity(
        self,
        identifier: str,
        project: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        context = get_context_from_identifier(identifier, project)
        _, entity_type, _, entity_name, entity_id = parse_identifier(
            identifier,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        unversioned: bool = kwargs.pop("unversioned", False)
        delete_all_versions: bool = kwargs.pop("delete_all_versions", False)

        if unversioned:
            if entity_id is None:
                entity_id = identifier
            op = BackendOp.DELETE
        else:
            if delete_all_versions:
                op = BackendOp.DELETE_ALL_VERSIONS
            else:
                if entity_id is None:
                    raise ValueError("If `delete_all_versions` is False, `entity_id` must be provided.")
                op = BackendOp.DELETE

        if op == BackendOp.DELETE:
            target = ContextEntityTarget(context.name, entity_type, entity_id)
            options = DeleteOptions(**kwargs)
        else:
            target = ContextCollectionTarget(context.name, entity_type)
            options = DeleteAllVersionsOptions(name=entity_name, **kwargs)
        return context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=op,
                target=target,
                options=options,
            )
        )
