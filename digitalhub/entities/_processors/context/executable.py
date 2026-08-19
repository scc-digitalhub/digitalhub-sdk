# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.utils import get_context, get_context_from_identifier
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.executable.protocol import ExecutableEntityProtocol
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor


class ContextEntityExecutableProcessor:
    """Processor for executable entity import and load operations."""

    def __init__(self, crud_processor: ContextEntityCRUDProcessor):
        self.crud_processor = crud_processor

    def import_executable_entity(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> ExecutableEntityProtocol:
        if (file is None) == (key is None):
            raise ValueError("Provide key or file, not both or none.")

        if file is not None:
            dict_obj: dict | list[dict] = read_yaml(file)
        else:
            ctx = get_context_from_identifier(key)
            dict_obj: dict = self.crud_processor._read_context_entity(ctx, key)

        if isinstance(dict_obj, list):
            exec_dict = dict_obj[0]
            exec_dict["status"] = {}
            tsk_dicts = []
            for item in dict_obj[1:]:
                item["status"] = {}
                tsk_dicts.append(item)
        else:
            exec_dict = dict_obj
            exec_dict["status"] = {}
            tsk_dicts = []

        if context is None:
            context = exec_dict["project"]

        ctx = get_context(context)
        obj: ExecutableEntityProtocol = entity_factory.build_entity_from_dict(exec_dict)

        if reset_id:
            new_id = build_uuid()
            obj.id = new_id
            obj.metadata.version = new_id

        try:
            bck_obj = self.crud_processor._create_context_entity(ctx, obj.ENTITY_TYPE, obj.to_dict())
            new_obj: ExecutableEntityProtocol = entity_factory.build_entity_from_dict(bck_obj)
        except EntityAlreadyExistsError:
            raise EntityError(f"Entity {obj.name} already exists. If you want to update it, use load instead.")

        new_obj.import_tasks(tsk_dicts)
        return new_obj

    def load_executable_entity(
        self,
        file: str,
    ) -> ExecutableEntityProtocol:
        dict_obj: dict | list[dict] = read_yaml(file)
        if isinstance(dict_obj, list):
            exec_dict = dict_obj[0]
            tsk_dicts = dict_obj[1:]
        else:
            exec_dict = dict_obj
            tsk_dicts = []

        context = get_context(exec_dict["project"])
        obj: ExecutableEntityProtocol = entity_factory.build_entity_from_dict(exec_dict)

        try:
            self.crud_processor._update_context_entity(context, obj.ENTITY_TYPE, obj.id, obj.to_dict())
        except EntityNotExistsError:
            self.crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())

        obj.import_tasks(tsk_dicts)
        return obj
