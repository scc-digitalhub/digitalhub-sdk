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
