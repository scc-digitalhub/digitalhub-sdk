# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._commons.keys import build_context_entity_key, build_project_key


def test_build_project_key_uses_store_scheme() -> None:
    assert build_project_key("project-id") == "store://project-id"


def test_build_context_entity_key_includes_name_and_id_when_provided() -> None:
    assert (
        build_context_entity_key(
            "project",
            "function",
            "python",
            "handler",
            "entity-id",
        )
        == "store://project/function/python/handler:entity-id"
    )


def test_build_context_entity_key_omits_id_when_not_provided() -> None:
    assert (
        build_context_entity_key("project", "task", "python+job", "task-id")
        == "store://project/task/python+job/task-id"
    )
