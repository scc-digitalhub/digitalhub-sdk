# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

import digitalhub.entities._processors.utils as processor_utils
from digitalhub.utils.exceptions import EntityError


def test_parse_identifier_parses_versioned_key() -> None:
    assert processor_utils.parse_identifier("store://project/function/python/pipeline:function-id") == (
        "project",
        "function",
        "python",
        "pipeline",
        "function-id",
    )


def test_parse_identifier_parses_unversioned_key() -> None:
    assert processor_utils.parse_identifier("store://project/task/python+job/task-id") == (
        "project",
        "task",
        "python+job",
        None,
        "task-id",
    )


def test_parse_identifier_parses_versioned_key_without_id() -> None:
    assert processor_utils.parse_identifier("store://project/function/python/pipeline") == (
        "project",
        "function",
        "python",
        "pipeline",
        None,
    )


def test_parse_identifier_preserves_colons_in_id() -> None:
    assert processor_utils.parse_identifier("store://project/function/python/pipeline:id:revision") == (
        "project",
        "function",
        "python",
        "pipeline",
        "id:revision",
    )


def test_parse_identifier_parses_log_key_as_unversioned() -> None:
    assert processor_utils.parse_identifier("store://project/log/log/log-id") == (
        "project",
        "log",
        "log",
        None,
        "log-id",
    )


def test_parse_identifier_uses_explicit_components_for_simple_identifier() -> None:
    assert processor_utils.parse_identifier(
        "pipeline",
        project="project",
        entity_type="function",
        entity_kind="python",
        entity_id="function-id",
    ) == ("project", "function", "python", "pipeline", "function-id")


def test_parse_identifier_requires_project_and_entity_type_for_simple_identifier() -> None:
    with pytest.raises(ValueError, match="Project and entity type must be specified"):
        processor_utils.parse_identifier("pipeline")


@pytest.mark.parametrize(
    ("identifier", "project", "expected_project"),
    [
        ("pipeline", "explicit-project", "explicit-project"),
        ("store://key-project/function/python/pipeline:function-id", None, "key-project"),
    ],
)
def test_get_context_from_identifier_resolves_project(
    identifier: str,
    project: str | None,
    expected_project: str,
    monkeypatch,
) -> None:
    get_context = Mock(return_value="context")
    monkeypatch.setattr(processor_utils, "get_context", get_context)

    assert processor_utils.get_context_from_identifier(identifier, project) == "context"
    get_context.assert_called_once_with(expected_project)


def test_get_context_from_identifier_requires_project_for_simple_identifier() -> None:
    with pytest.raises(EntityError, match="Specify project if you do not specify entity key"):
        processor_utils.get_context_from_identifier("pipeline")


@pytest.mark.parametrize(
    ("project", "entity_type", "message"),
    [
        ("other-project", "function", "belongs to project 'key-project', not 'other-project'"),
        ("key-project", "workflow", "is of type 'function', not 'workflow'"),
    ],
)
def test_parse_identifier_rejects_a_key_that_contradicts_the_arguments(
    project: str, entity_type: str, message: str
) -> None:
    # The key used to win silently: delete_workflow(<key of a function>) deleted the function.
    with pytest.raises(ValueError, match=message):
        processor_utils.parse_identifier(
            "store://key-project/function/python/pipeline:function-id",
            project=project,
            entity_type=entity_type,
        )


def test_parse_identifier_accepts_arguments_that_match_the_key() -> None:
    assert processor_utils.parse_identifier(
        "store://key-project/function/python/pipeline:function-id",
        project="key-project",
        entity_type="function",
    ) == ("key-project", "function", "python", "pipeline", "function-id")


def test_get_context_from_identifier_rejects_a_key_of_another_project(monkeypatch) -> None:
    get_context = Mock()
    monkeypatch.setattr(processor_utils, "get_context", get_context)

    with pytest.raises(ValueError, match="belongs to project 'key-project', not 'other-project'"):
        processor_utils.get_context_from_identifier(
            "store://key-project/function/python/pipeline:function-id", "other-project"
        )
    get_context.assert_not_called()
