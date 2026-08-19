# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.generic.entity import GenericMixin
from digitalhub.entities.dataitem._base.entity import Dataitem

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.generic.spec import GenericSpec
    from digitalhub.entities._mixin.generic.status import GenericStatus


class DataitemGeneric(Dataitem, GenericMixin):
    """Generic dataitem entity that preserves runtime fields without dataitem-specific methods."""

    ENTITY_TYPE = EntityTypes.DATAITEM.value

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: GenericSpec
        self.status: GenericStatus
