# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities.builders import generic_entity_builders
from digitalhub.utils.exceptions import EntityError

ArtifactGenericBuilder = dict(generic_entity_builders)[EntityTypes.ARTIFACT.value]


def test_artifact_generic_builder_accepts_version_and_arbitrary_spec_fields() -> None:
    artifact = ArtifactGenericBuilder().build(
        kind="artifact",
        project="my-project",
        name="my-artifact",
        path="artifact.bin",
        version="1.2.3",
        future_backend_field={"enabled": True},
    )

    assert artifact.metadata.version == "1.2.3"
    assert artifact.spec.future_backend_field == {"enabled": True}


def test_artifact_builder_keeps_extensions_and_requires_path() -> None:
    artifact = ArtifactGenericBuilder().build(
        kind="artifact",
        project="my-project",
        name="my-artifact",
        path="artifact.bin",
        extensions=[{"key": "value"}],
    )

    assert artifact.extensions == [{"key": "value"}]
    assert artifact.to_dict()["extensions"] == [{"key": "value"}]
    with pytest.raises(EntityError, match="Path must be provided"):
        ArtifactGenericBuilder().build(kind="artifact", project="my-project", name="my-artifact")
