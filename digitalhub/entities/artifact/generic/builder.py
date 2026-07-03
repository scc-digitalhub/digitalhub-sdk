from __future__ import annotations

import typing

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._base.material.builder import MaterialBuilder
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.artifact.generic.entity import ArtifactGeneric
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact.generic.entity import ArtifactGeneric as ArtifactGenericType


class ArtifactGenericBuilder(GenericBuilder, MaterialBuilder):
    """Builder for generic artifacts that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.ARTIFACT.value
    ENTITY_CLASS = ArtifactGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value

    def build(
        self,
        kind: str,
        project: str,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        extensions: list[dict] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> ArtifactGenericType:
        if path is None:
            raise EntityError("Path must be provided.")

        name = self.build_name(name)
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=name,
            description=description,
            labels=labels,
            embedded=embedded,
        )
        spec = self.build_spec(
            path=path,
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
            extensions=extensions,
        )
