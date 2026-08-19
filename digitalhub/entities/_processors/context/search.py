# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
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
        kwargs = context.client.build_parameters(
            ApiCategories.CONTEXT.value,
            BackendOperations.SEARCH.value,
            query=query,
            entity_types=entity_types,
            name=name,
            kind=kind,
            created=created,
            updated=updated,
            description=description,
            labels=labels,
            **kwargs,
        )
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.SEARCH.value,
            project=context.name,
        )
        entities_dict = context.client.read_object(api, **kwargs)
        living_entities = []
        dead_entities = []
        for entity in entities_dict["content"]:
            try:
                living_entity = crud_processor.read_context_entity(entity["key"])
                living_entities.append(living_entity)
            except BackendError:
                logger.debug(
                    f"Entity '{entity.get('key', 'unknown')}' could not be read from backend",
                    exc_info=True,
                )
                dead_entities.append(entity)
        return living_entities, dead_entities
