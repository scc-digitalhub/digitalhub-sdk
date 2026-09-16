# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import NoOptions, ShareOptions
from digitalhub.stores.client.compiler.targets import BaseEntityTarget
from digitalhub.stores.client.factory import get_client


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
        target = BaseEntityTarget(entity_type, entity_name)
        entity_id = None

        if unshare:
            users = client.execute(
                ClientOp(
                    category=ApiType.BASE,
                    operation=BackendOp.SHARE_READ,
                    target=target,
                    options=NoOptions(),
                )
            )
            for u in users:
                if u["user"] == user:
                    entity_id = u["id"]
                    break
            else:
                raise ValueError(f"User '{user}' does not have access to project.")

        options = ShareOptions(user=user, unshare=unshare, share_id=entity_id, role=role)
        if unshare:
            client.execute(
                ClientOp(
                    category=ApiType.BASE,
                    operation=BackendOp.UNSHARE,
                    target=target,
                    options=options,
                )
            )
            return
        client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.SHARE,
                target=target,
                options=options,
                payload={},
            )
        )
