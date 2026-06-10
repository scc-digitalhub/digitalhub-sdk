# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.versioned.builder import VersionedBuilder
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.image._base.entity import Image
from digitalhub.entities.image._base.spec import ImageSpec, ImageValidator
from digitalhub.entities.image._base.status import ImageStatus


class ImageImageBuilder(VersionedBuilder):
    """
    ImageImageBuilder builder.
    """

    ENTITY_TYPE = EntityTypes.IMAGE.value
    ENTITY_CLASS = Image
    ENTITY_SPEC_CLASS = ImageSpec
    ENTITY_SPEC_VALIDATOR = ImageValidator
    ENTITY_STATUS_CLASS = ImageStatus
    ENTITY_KIND = EntityKinds.IMAGE_IMAGE.value

    def build(
        self,
        kind: str,
        project: str,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> Image:
        """
        Create a new object.

        Parameters
        ----------
        project : str
            Project name.
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Image
            Object instance.
        """
        name = self.build_name(name)
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=name,
            description=description,
            labels=labels,
        )
        path = f"image://{name}"
        provider = "kubernetes"
        spec = self.build_spec(
            path=path,
            provider=provider,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            project=project,
            name=name,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )
