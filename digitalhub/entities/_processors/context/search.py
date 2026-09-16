# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._processors.utils import get_context, parse_identifier
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import ctx_ra
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor

logger = get_logger(__name__)


class ContextEntitySearchProcessor:
    def search_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        project: str,
        query: str | None = None,
        entity_types: list[str] | None = None,
        name: str | None = None,
        kind: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> tuple[list[ContextEntity], list[dict]]:
        context = get_context(project)
        params = {
            **kwargs,
            "query": query,
            "entity_types": entity_types,
            "name": name,
            "kind": kind,
            "created": created,
            "updated": updated,
            "description": description,
            "labels": labels,
        }
        entities_dict = context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.SEARCH,
                route_args=ctx_ra(context.name),
                params=params,
            )
        )
        living_entities = []
        dead_entities = []
        for entity in entities_dict["content"]:
            try:
                _, entity_type, _, _, _ = parse_identifier(entity["key"])
                living_entity = crud_processor.read_context_entity(entity["key"], entity_type=entity_type)
                living_entities.append(living_entity)
            except BackendError:
                logger.debug(
                    f"Entity '{entity.get('key', 'unknown')}' could not be read from backend",
                    exc_info=True,
                )
                dead_entities.append(entity)
        return living_entities, dead_entities
