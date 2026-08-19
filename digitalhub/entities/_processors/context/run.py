# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities.log._base.entity import Log

logger = get_logger(__name__)


class ContextEntityRunProcessor:
    def read_run_logs(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> list[Log]:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.LOGS.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        objects: list[dict] = context.client.read_object(api, **kwargs)
        logs = []
        for o in objects:
            content = o.pop("content", None)
            o["kind"] = EntityKinds.LOG_LOG.value
            entity: Log = entity_factory.build_entity_from_dict(o)
            entity.set_content(content)
            logs.append(entity)
        return logs

    def stop_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> None:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.STOP.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        context.client.create_object(api, obj={}, **kwargs)

    def resume_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> None:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.RESUME.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        context.client.create_object(api, obj={}, **kwargs)
