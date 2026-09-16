# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import ctx_entity_id_ra
from digitalhub.stores.client.compiler.operation import ClientOp
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
        state: str | None = None,
    ) -> list[Log]:
        objects: list[dict] = get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.LOGS_READ,
                route_args=ctx_entity_id_ra(project, entity_type, entity_id),
                params={"state": state} if state is not None else {},
            )
        )
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
        reason: str | None = None,
    ) -> None:
        get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.STOP,
                route_args=ctx_entity_id_ra(project, entity_type, entity_id),
                payload={},
                params={"reason": reason} if reason is not None else {},
            )
        )

    def resume_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        reason: str | None = None,
    ) -> None:
        get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.RESUME,
                route_args=ctx_entity_id_ra(project, entity_type, entity_id),
                payload={},
                params={"reason": reason} if reason is not None else {},
            )
        )
