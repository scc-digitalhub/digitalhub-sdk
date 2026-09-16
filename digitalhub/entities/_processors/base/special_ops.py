# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.factory import get_client
from digitalhub.stores.client.common.enums import ApiType, BEOps
from digitalhub.stores.client.compiler.apis.utils import base_entity_ra
from digitalhub.stores.client.compiler.operation import ClientOp


class BaseEntitySpecialOpsProcessor:
    def build_project_key(self, entity_id: str) -> str:
        return f"store://{entity_id}"

    def share_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        user: str,
        unshare: bool = False,
        role: str | None = None,
    ) -> None:
        client = get_client()
        route_args = base_entity_ra(entity_type, entity_name)
        entity_id = None

        if unshare:
            users = client.execute(
                ClientOp(
                    category=ApiType.BASE,
                    operation=BEOps.SHARE_READ,
                    route_args=route_args,
                )
            )
            for u in users:
                if u["user"] == user:
                    entity_id = u["id"]
                    break
            else:
                raise ValueError(f"User '{user}' does not have access to project.")

        params = {"unshare": unshare, "user": user}
        if entity_id is not None:
            params["id"] = entity_id
        if role is not None:
            params["role"] = role
        if unshare:
            client.execute(
                ClientOp(
                    category=ApiType.BASE,
                    operation=BEOps.UNSHARE,
                    route_args=route_args,
                    params=params,
                )
            )
            return
        client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BEOps.SHARE,
                route_args=route_args,
                params=params,
                payload={},
            )
        )
