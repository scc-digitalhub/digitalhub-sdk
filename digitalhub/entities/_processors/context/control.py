# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import StopResumeOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget


class ContextEntityControlProcessor:
    """Processor for shared context entity lifecycle controls."""

    def stop_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        reason: str | None = None,
    ) -> None:
        self._change_entity_state(BackendOp.STOP, project, entity_type, entity_id, reason)

    def resume_entity(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        reason: str | None = None,
    ) -> None:
        self._change_entity_state(BackendOp.RESUME, project, entity_type, entity_id, reason)

    @staticmethod
    def _change_entity_state(
        operation: BackendOp,
        project: str,
        entity_type: str,
        entity_id: str,
        reason: str | None,
    ) -> None:
        get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=operation,
                target=ContextEntityTarget(project, entity_type, entity_id),
                payload={},
                options=StopResumeOptions(reason=reason),
            )
        )
