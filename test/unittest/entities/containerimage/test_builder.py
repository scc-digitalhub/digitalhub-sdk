# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.factory.registry import registry


def test_containerimage_builder_routes_embedded_to_metadata() -> None:
    builder = registry.get_entity_builder(EntityKinds.CONTAINERIMAGE_CONTAINERIMAGE.value)
    containerimage = builder.build(
        project="project",
        name="image",
        kind=builder.ENTITY_KIND,
        image="registry.example.com/image:latest",
        embedded=True,
    )

    assert containerimage.metadata.embedded is True
    assert "embedded" not in containerimage.spec.to_dict()
