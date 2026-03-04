# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.extension._base.spec import ExtensionSpec
    from digitalhub.entities.extension._base.status import ExtensionStatus


class Extension(VersionedEntity):
    """
    A class representing a extension.
    """

    ENTITY_TYPE = EntityTypes.EXTENSION.value

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.spec: ExtensionSpec
        self.status: ExtensionStatus
