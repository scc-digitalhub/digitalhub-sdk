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
        data = get_context(obj.project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.DATA_READ,
                target=ContextCollectionTarget(obj.project, obj.ENTITY_TYPE),
                options=OpaqueOptions({"keys": obj.name}),
            )
        )
        return data[obj.name]

    def set_secret_value(self, obj: Secret, value: str) -> None:
        get_context(obj.project).client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.DATA_UPDATE,
                target=ContextCollectionTarget(obj.project, obj.ENTITY_TYPE),
                payload={obj.name: value},
            )
        )
