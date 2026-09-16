# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions, StopResumeOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
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
                operation=BackendOp.LOGS_READ,
                target=ContextEntityTarget(project, entity_type, entity_id),
                options=LogsOptions(state=state),
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
                operation=BackendOp.STOP,
                payload={},
                target=ContextEntityTarget(project, entity_type, entity_id),
                options=StopResumeOptions(reason=reason),
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
                operation=BackendOp.RESUME,
                payload={},
                target=ContextEntityTarget(project, entity_type, entity_id),
                options=StopResumeOptions(reason=reason),
            )
        )
