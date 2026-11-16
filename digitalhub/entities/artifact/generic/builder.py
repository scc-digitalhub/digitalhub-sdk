# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._mixin.generic.builder import GenericBuilder
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities.artifact._base.builder import ArtifactBuilder
from digitalhub.entities.artifact.generic.entity import ArtifactGeneric


class ArtifactGenericBuilder(GenericBuilder, ArtifactBuilder):
    """Builder for generic artifacts that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.ARTIFACT.value
    ENTITY_CLASS = ArtifactGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
