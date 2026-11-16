# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities.artifact._base.builder import ArtifactBuilder
from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact
from digitalhub.entities.artifact.artifact.spec import ArtifactSpecArtifact
from digitalhub.entities.artifact.artifact.status import ArtifactStatusArtifact


class ArtifactArtifactBuilder(ArtifactBuilder):
    """
    ArtifactArtifact builder.
    """

    ENTITY_CLASS = ArtifactArtifact
    ENTITY_SPEC_CLASS = ArtifactSpecArtifact
    ENTITY_STATUS_CLASS = ArtifactStatusArtifact
    ENTITY_KIND = EntityKinds.ARTIFACT_ARTIFACT.value
