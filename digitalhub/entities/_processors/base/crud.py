# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from digitalhub.context.api import build_context, delete_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import DeleteOptions
from digitalhub.stores.client.compiler.targets import BaseCollectionTarget, BaseEntityTarget
from digitalhub.stores.client.factory import resolve_client
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project
    from digitalhub.stores.client.client import Client


class BaseEntityCRUDProcessor:
    @staticmethod
    def _registered(obj: dict) -> Project:
        """
        Build a project from backend state and register its context.

        Contexts change only here, with what the backend returned: building a
        project elsewhere, from a listing or a YAML file, leaves them alone.
        """
        project = typing.cast("Project", entity_factory.build_entity_from_dict(obj))
        build_context(project)
        return project

    def _create_base_entity(self, client: Client, entity_type: str, entity_dict: dict) -> dict:
        return client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.CREATE,
                target=BaseCollectionTarget(entity_type),
                payload=entity_dict,
            )
        )

    def create_project_entity(self, _entity: Project | None = None, **kwargs) -> Project:
        if _entity is not None:
            client = _entity._client
            obj = _entity
        else:
            client = resolve_client()
            obj = entity_factory.build_entity_from_params(**kwargs)
        ent = self._create_base_entity(client, obj.ENTITY_TYPE, obj.to_dict())
        return self._registered(ent)

    def _read_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_name: str,
    ) -> dict:
        return client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.READ,
                target=BaseEntityTarget(entity_type, entity_name),
            )
        )

    def read_project_entity(self, entity_type: str, entity_name: str) -> Project:
        client = resolve_client()
        obj = self._read_base_entity(client, entity_type, entity_name)
        return self._registered(obj)

    def _list_base_entities(self, client: Client, entity_type: str) -> list[dict]:
        return client.execute_list(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.LIST,
                target=BaseCollectionTarget(entity_type),
            )
        )

    def list_project_entities(self, entity_type: str) -> list[Project]:
        client = resolve_client()
        objs = self._list_base_entities(client, entity_type)
        entities = []
        for obj in objs:
            ent = entity_factory.build_entity_from_dict(obj)
            entities.append(ent)
        return entities

    def import_project_entity(self, file: str, **kwargs) -> Project:
        obj: dict = read_yaml(file)
        obj["status"] = {}
        ent: Project = entity_factory.build_entity_from_dict(obj)
        reset_id = kwargs.pop("reset_id", False)

        try:
            created = self._create_base_entity(ent._client, ent.ENTITY_TYPE, ent.to_dict())
        except EntityAlreadyExistsError:
            msg = f"Entity {ent.name} already exists."
            if reset_id:
                self.read_project_entity(ent.ENTITY_TYPE, ent.name)
                ent._import_entities(obj, reset_id=reset_id)
                warn(f"{msg} Other entities ids have been imported.")
                ent.refresh()
                return ent
            raise EntityError(f"{msg} If you want to update it, use load instead.")

        self._registered(created)
        ent._import_entities(obj, reset_id=reset_id)
        ent.refresh()
        return ent

    def load_project_entity(self, file: str) -> Project:
        obj: dict = read_yaml(file)
        ent: Project = entity_factory.build_entity_from_dict(obj)

        try:
            stored = self._update_base_entity(ent._client, ent.ENTITY_TYPE, ent.name, ent.to_dict())
        except EntityNotExistsError:
            stored = self._create_base_entity(ent._client, ent.ENTITY_TYPE, ent.to_dict())

        self._registered(stored)
        ent._load_entities(obj)
        ent.refresh()
        return ent

    def _update_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_name: str,
        entity_dict: dict,
    ) -> dict:
        return client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.UPDATE,
                target=BaseEntityTarget(entity_type, entity_name),
                payload=entity_dict,
            )
        )

    def update_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        entity_dict: dict,
    ) -> Project:
        client = resolve_client()
        obj = self._update_base_entity(client, entity_type, entity_name, entity_dict)
        return self._registered(obj)

    def _delete_base_entity(
        self,
        client: Client,
        entity_type: str,
        entity_name: str,
        cascade: bool,
    ) -> dict:
        return client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.DELETE,
                target=BaseEntityTarget(entity_type, entity_name),
                options=DeleteOptions(cascade=cascade),
            )
        )

    def delete_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        cascade: bool = True,
        clean_context: bool = True,
    ) -> dict:
        client = resolve_client()
        response = self._delete_base_entity(client, entity_type, entity_name, cascade)
        if clean_context:
            delete_context(entity_name)
        return response
