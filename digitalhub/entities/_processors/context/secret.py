# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._processors.utils import get_context
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import OpaqueOptions
from digitalhub.stores.client.compiler.targets import ContextCollectionTarget

if typing.TYPE_CHECKING:
    from digitalhub.entities.secret._base.entity import Secret


class ContextEntitySecretProcessor:
    def read_secret_value(self, obj: Secret) -> str:
        data = self._read_secret_data(
            obj.project,
            obj.ENTITY_TYPE,
            params={"keys": obj.name},
        )
        return data[obj.name]

    def set_secret_value(self, obj: Secret, value: str) -> None:
        self._update_secret_data(
            obj.project,
            obj.ENTITY_TYPE,
            {obj.name: value},
        )

    def _read_secret_data(
        self,
        project: str,
        entity_type: str,
        params: dict | None = None,
    ) -> dict:
        return get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.DATA_READ,
                target=ContextCollectionTarget(project, entity_type),
                options=OpaqueOptions(params or {}),
            )
        )

    def _update_secret_data(
        self,
        project: str,
        entity_type: str,
        data: dict,
    ) -> None:
        get_context(project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.DATA_UPDATE,
                target=ContextCollectionTarget(project, entity_type),
                payload=data,
            )
        )
