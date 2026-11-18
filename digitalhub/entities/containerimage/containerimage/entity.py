# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities.containerimage._base.entity import Containerimage

if typing.TYPE_CHECKING:
    from digitalhub.entities.containerimage._base.spec import ContainerimageSpec
    from digitalhub.entities.containerimage._base.status import ContainerimageStatus


class ContainerimageContainerimage(Containerimage):
    """
    A class representing a image.
    """

    ENTITY_TYPE = EntityTypes.CONTAINERIMAGE.value

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.spec: ContainerimageSpec
        self.status: ContainerimageStatus
