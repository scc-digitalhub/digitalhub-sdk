# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.factory.registry import registry


def test_secret_builder_routes_embedded_to_metadata() -> None:
    secret = registry.get_entity_builder(EntityKinds.SECRET_SECRET.value).build(
        project="project",
        name="secret",
        kind=EntityKinds.SECRET_SECRET.value,
        embedded=True,
    )

    assert secret.metadata.embedded is True
    assert "embedded" not in secret.spec.to_dict()
