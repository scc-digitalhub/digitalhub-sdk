# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities.containerimage.containerimage.builder import ContainerimageContainerimageBuilder


def test_containerimage_builder_routes_embedded_to_metadata() -> None:
    builder = ContainerimageContainerimageBuilder()
    containerimage = builder.build(
        project="project",
        name="image",
        kind=builder.ENTITY_KIND,
        image="registry.example.com/image:latest",
        embedded=True,
    )

    assert containerimage.metadata.embedded is True
    assert "embedded" not in containerimage.spec.to_dict()
