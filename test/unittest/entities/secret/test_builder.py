# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities.secret._base.builder import SecretSecretBuilder


def test_secret_builder_routes_embedded_to_metadata() -> None:
    secret = SecretSecretBuilder().build(
        project="project",
        name="secret",
        kind=SecretSecretBuilder.ENTITY_KIND,
        embedded=True,
    )

    assert secret.metadata.embedded is True
    assert "embedded" not in secret.spec.to_dict()
