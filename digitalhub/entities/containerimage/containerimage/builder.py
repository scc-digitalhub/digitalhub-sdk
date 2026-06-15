# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.containerimage._base.entity import Containerimage
from digitalhub.entities.containerimage._base.spec import ContainerimageSpec, ContainerimageValidator
from digitalhub.entities.containerimage._base.status import ContainerimageStatus


class ContainerimageContainerimageBuilder(ContainerimageBuilder):
    """
    ContainerimageContainerimageBuilder builder.
    """

    ENTITY_CLASS = Containerimage
    ENTITY_SPEC_CLASS = ContainerimageSpec
    ENTITY_SPEC_VALIDATOR = ContainerimageValidator
    ENTITY_STATUS_CLASS = ContainerimageStatus
    ENTITY_KIND = EntityKinds.CONTAINERIMAGE_CONTAINERIMAGE.value
