# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.utils import is_valid_key, sanitize_unversioned_key
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.utils import (
    get_context,
    get_context_from_identifier,
    parse_identifier,
)
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import (
    ctx_entity_id_ra,
    ctx_entity_ra,
)
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.utils.exceptions import BuilderError, EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml, write_yaml

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._mixin.unversioned.protocol import UnversionedEntityProtocol


class ContextEntityCRUDProcessor:
    def _create_context_entity(
        self,
        context: Context,
        entity_type: str,
        entity_dict: dict,
    ) -> dict:
        return context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.CREATE,
                route_args=ctx_entity_ra(context.name, entity_type),
                payload=entity_dict,
            )
        )

    def create_context_entity(
        self,
        _entity: ContextEntity | None = None,
        **kwargs,
    ) -> ContextEntity:
        if _entity is not None:
            context = _entity._context()
            obj = _entity
        else:
            context = get_context(kwargs["project"])
            entity_kind = kwargs.get("kind")
            entity_type = kwargs.pop("entity_type")
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
        new_obj = self._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        return entity_factory.build_entity_from_dict(new_obj, entity_type=obj.ENTITY_TYPE)

    def export_context_entity(self, _entity: ContextEntity) -> str:
        obj = _entity.to_dict()
        pth = _entity._context().root / f"{_entity.ENTITY_TYPE}s-{_entity.id}.yaml"
        write_yaml(pth, obj)
        return str(pth)

    def _read_context_entity(
        self,
        context: Context,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        project, entity_type, _, entity_name, entity_id = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        if entity_id is None:
            kwargs["name"] = entity_name
            return context.client.execute_first(
                ClientOp(
                    category=ApiType.CONTEXT,
                    operation=BEOps.LIST,
                    route_args=ctx_entity_ra(context.name, entity_type),
                    params=kwargs,
                )
            )

        return context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.READ,
                route_args=ctx_entity_id_ra(context.name, entity_type, entity_id),
                params=kwargs,
            )
        )

    def read_context_entity(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> ContextEntity:
        context = get_context_from_identifier(identifier, project)
        obj = self._read_context_entity(
            context,
            identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )
        entity = entity_factory.build_entity_from_dict(obj, entity_type=entity_type)
        entity._post_read_hook()
        return entity

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
        else:
            identifier = sanitize_unversioned_key(identifier)
        return self.read_context_entity(
            identifier,
            entity_type=entity_type,
            project=project,
            entity_id=entity_id,
            **kwargs,
        )

    def _read_context_entity_versions(
        self,
        context: Context,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        **kwargs,
    ) -> list[dict]:
        project, entity_type, _, entity_name, _ = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
        )

        params = {**kwargs, "name": entity_name, "versions": "all"}
        return context.client.execute_list(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.LIST,
                route_args=ctx_entity_ra(context.name, entity_type),
                params=params,
            )
        )

    def read_context_entity_versions(
        self,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        **kwargs,
    ) -> list[ContextEntity]:
        context = get_context_from_identifier(identifier, project)
        objs = self._read_context_entity_versions(
            context,
            identifier,
            entity_type=entity_type,
            project=project,
            **kwargs,
        )
        objects = []
        for o in objs:
            _, entity_type, _, _, _ = parse_identifier(o["key"])
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
            ctx = get_context_from_identifier(key)
            dict_obj = self._read_context_entity(ctx, key)

        dict_obj["status"] = {}

        if context is None:
            context = dict_obj["project"]

        _, entity_type, _, _, _ = parse_identifier(dict_obj["key"])

        ctx = get_context(context)
        obj = entity_factory.build_entity_from_dict(dict_obj, entity_type=entity_type)
        if reset_id:
            new_id = build_uuid()
            obj.id = new_id
            obj.metadata.version = new_id
        try:
            bck_obj = self._create_context_entity(ctx, obj.ENTITY_TYPE, obj.to_dict())
            new_obj: ContextEntity = entity_factory.build_entity_from_dict(bck_obj, entity_type=entity_type)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")
        return new_obj

    def load_context_entity(
        self,
        file: str,
    ) -> ContextEntity:
        dict_obj: dict = read_yaml(file)
        context = get_context(dict_obj["project"])
        _, entity_type, _, _, _ = parse_identifier(dict_obj["key"])
        obj: ContextEntity = entity_factory.build_entity_from_dict(dict_obj, entity_type=entity_type)
        try:
            self._update_context_entity(context, obj.ENTITY_TYPE, obj.id, obj.to_dict())
        except EntityNotExistsError:
            self._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        return obj

    def _list_context_entities(
        self,
        context: Context,
        entity_type: str,
        **kwargs,
    ) -> list[dict]:
        return context.client.execute_list(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.LIST,
                route_args=ctx_entity_ra(context.name, entity_type),
                params=kwargs,
            )
        )

    def list_context_entities(
        self,
        project: str,
        entity_type: str,
        **kwargs,
    ) -> list[ContextEntity]:
        context = get_context(project)
        objs = self._list_context_entities(context, entity_type, **kwargs)
        objects = []
        for o in objs:
            entity: ContextEntity = entity_factory.build_entity_from_dict(o, entity_type=entity_type)
            objects.append(entity)
        return objects

    def _update_context_entity(
        self,
        context: Context,
        entity_type: str,
        entity_id: str,
        entity_dict: dict,
    ) -> dict:
        return context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.UPDATE,
                route_args=ctx_entity_id_ra(context.name, entity_type, entity_id),
                payload=entity_dict,
            )
        )

    def update_context_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_dict: dict,
    ) -> ContextEntity:
        context = get_context(project)
        obj = self._update_context_entity(
            context,
            entity_type,
            entity_id,
            entity_dict,
        )
        return entity_factory.build_entity_from_dict(obj, entity_type=entity_type)

    def _delete_context_entity(
        self,
        context: Context,
        identifier: str,
        entity_type: str | None = None,
        project: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        project, entity_type, _, entity_name, entity_id = parse_identifier(
            identifier,
            project=project,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        unversioned: bool = kwargs.pop("unversioned", False)
        delete_all_versions: bool = kwargs.pop("delete_all_versions", False)

        if unversioned:
            if entity_id is None:
                entity_id = identifier
            op = BEOps.DELETE
        else:
            if delete_all_versions:
                op = BEOps.DELETE_ALL_VERSIONS
                kwargs["name"] = entity_name
            else:
                if entity_id is None:
                    raise ValueError("If `delete_all_versions` is False, `entity_id` must be provided.")
                op = BEOps.DELETE

        if op == BEOps.DELETE:
            route_args = ctx_entity_id_ra(context.name, entity_type, entity_id)
        else:
            route_args = ctx_entity_ra(context.name, entity_type)
        return context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=op,
                route_args=route_args,
                params=kwargs,
            )
        )

    def delete_context_entity(
        self,
        identifier: str,
        project: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        **kwargs,
    ) -> dict:
        context = get_context_from_identifier(identifier, project)
        return self._delete_context_entity(
            context,
            identifier,
            entity_type,
            context.name,
            entity_id,
            **kwargs,
        )
