# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import ctx_entity_ra
from digitalhub.stores.client.compiler.operation import ClientOp


class ContextEntitySecretProcessor:
    def read_secret_data(
        self,
        project: str,
        entity_type: str,
        params: dict | None = None,
    ) -> dict:
        return get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.DATA_READ,
                route_args=ctx_entity_ra(project, entity_type),
                params={"params": params or {}},
            )
        )

    def update_secret_data(
        self,
        project: str,
        entity_type: str,
        data: dict,
    ) -> None:
        get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BEOps.DATA_UPDATE,
                route_args=ctx_entity_ra(project, entity_type),
                payload=data,
            )
        )
