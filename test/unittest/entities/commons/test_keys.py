# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from digitalhub.entities._commons.keys import EntityKey, EntityRef, build_project_key, is_valid_key


def test_build_project_key_uses_store_scheme() -> None:
    assert build_project_key("project-id") == "store://project-id"


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (
            "store://project/function/python/handler:entity-id",
            EntityKey("project", "function", "python", "handler", "entity-id"),
        ),
        ("store://project/function/python/handler", EntityKey("project", "function", "python", "handler")),
        ("store://project/task/python+job/task-id", EntityKey("project", "task", "python+job", id="task-id")),
        (
            "store://project/run/mlflowserve+serve:run/run-id",
            EntityKey("project", "run", "mlflowserve+serve:run", id="run-id"),
        ),
        ("store://project/log/log/log-id", EntityKey("project", "log", "log", id="log-id")),
    ],
)
def test_entity_key_round_trip(key: str, expected: EntityKey) -> None:
    assert EntityKey.parse(key) == expected
    assert str(expected) == key


def test_entity_key_reads_the_relationship_form_of_unversioned_keys() -> None:
    assert EntityKey.parse("store://project/run/python+run/run-id:run-id") == EntityKey(
        "project", "run", "python+run", id="run-id"
    )


def test_entity_key_keeps_colons_in_the_id() -> None:
    assert EntityKey.parse("store://project/function/python/pipeline:id:revision").id == "id:revision"


@pytest.mark.parametrize("key", ["pipeline", "store://project", "store://project/function/python", "s3://bucket/a/b/c"])
def test_entity_key_rejects_malformed_keys(key: str) -> None:
    assert not is_valid_key(key)
    with pytest.raises(ValueError, match=f"Invalid entity key '{key}'"):
        EntityKey.parse(key)


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("python://project/pipeline:function-id", EntityRef("python", "project", id="function-id", name="pipeline")),
        ("python+job://project/task-id", EntityRef("python+job", "project", id="task-id")),
    ],
)
def test_entity_ref_round_trip(ref: str, expected: EntityRef) -> None:
    assert EntityRef.parse(ref) == expected
    assert str(expected) == ref


@pytest.mark.parametrize(
    "ref", ["", "task-id", "task://project/", "function://project/:id", "function://project/name:"]
)
def test_entity_ref_rejects_malformed_references(ref: str) -> None:
    with pytest.raises(ValueError, match="Invalid entity reference"):
        EntityRef.parse(ref)
