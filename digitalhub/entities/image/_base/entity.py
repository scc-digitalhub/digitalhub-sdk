# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.image._base.spec import ImageSpec
    from digitalhub.entities.image._base.status import ImageStatus


class Image(VersionedEntity):
    """
    A class representing a image.
    """

    ENTITY_TYPE = EntityTypes.IMAGE.value

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.spec: ImageSpec
        self.status: ImageStatus
