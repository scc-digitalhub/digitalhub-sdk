# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.versioned.builder import VersionedBuilder
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities.containerimage._base.entity import Containerimage


class ContainerimageBuilder(VersionedBuilder):
    """
    Containerimage builder.
    """

    ENTITY_TYPE = EntityTypes.CONTAINERIMAGE.value

    def build(self, kind: str, project: str, name: str, *, image: str | None = None, **kwargs) -> Containerimage:
        """
        Create a new container image.

        Parameters
        ----------
        kind : str
            Kind the object.
        project : str
            Project name.
        name : str
            Object name.
        image : str
            Image URI.
        **kwargs : dict
            Other parameters of ``VersionedBuilder.build()``, then spec keyword arguments.

        Returns
        -------
        Containerimage
            Object instance.
        """
        if image is None:
            raise EntityError("Missing required 'image' argument.")
        return super().build(kind, project, name, image=image, **kwargs)
