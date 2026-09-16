# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.stores.client.compiler.apis.utils import (
    base_entity_ra,
    base_ra,
    ctx_entity_id_ra,
    ctx_entity_ra,
    ctx_metric_ra,
    ctx_ra,
)


def test_ra_builders() -> None:
    assert base_ra("project") == {"entity_type": "project"}
    assert base_entity_ra("project", "demo") == {
        "entity_type": "project",
        "entity_name": "demo",
    }
    assert ctx_ra("demo") == {"project": "demo"}
    assert ctx_entity_ra("demo", "artifact") == {
        "project": "demo",
        "entity_type": "artifact",
    }
    assert ctx_entity_id_ra("demo", "artifact", "artifact-id") == {
        "project": "demo",
        "entity_type": "artifact",
        "entity_id": "artifact-id",
    }
    assert ctx_metric_ra("demo", "run", "run-id", None) == {
        "project": "demo",
        "entity_type": "run",
        "entity_id": "run-id",
        "metric_name": None,
    }
