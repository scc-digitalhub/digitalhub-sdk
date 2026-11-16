# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities.artifact.generic.builder import ArtifactGenericBuilder


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
