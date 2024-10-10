from __future__ import annotations

import typing

from digitalhub.entities._base.entity.material import MaterialEntity
from digitalhub.entities.entity_types import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.metadata import Metadata
    from digitalhub.entities.artifact.spec import ArtifactSpec
    from digitalhub.entities.artifact.status import ArtifactStatus


class Artifact(MaterialEntity):
    """
    A class representing a artifact.

    Artifacts are (binary) objects stored in one of the artifact
    stores of the platform, and available to every process, module
    and component as files.
    """

    ENTITY_TYPE = EntityTypes.ARTIFACT.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: ArtifactSpec,
        status: ArtifactStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: ArtifactSpec
        self.status: ArtifactStatus
