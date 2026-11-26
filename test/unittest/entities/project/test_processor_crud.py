# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities.project._base.processor as base_crud_module
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.utils.exceptions import EntityError


def test_delete_project_preserves_context_when_backend_delete_fails(monkeypatch) -> None:
    processor = ProjectProcessor()
    client = Mock()
    client.execute.side_effect = RuntimeError("delete failed")
    delete_context = Mock()
    monkeypatch.setattr(base_crud_module, "delete_context", delete_context)
    monkeypatch.setattr(base_crud_module, "resolve_client", Mock(return_value=client))

    with pytest.raises(RuntimeError, match="delete failed"):
        processor.delete_project_entity("project", "example")

    delete_context.assert_not_called()


def test_refresh_reads_the_project_and_updates_the_same_object() -> None:
    processor = ProjectProcessor()
    processor.read_project_entity = Mock(return_value="fresh")
    project = Mock(ENTITY_TYPE="project")
    project.name = "demo"

    assert processor.refresh_project_entity(project) is project

    processor.read_project_entity.assert_called_once_with("project", "demo")
    project._update_attributes.assert_called_once_with("fresh")
    project.refresh.assert_not_called()


def test_create_project_entity_from_params_builds_the_project_and_creates_it(monkeypatch) -> None:
    processor = ProjectProcessor()
    processor.create_project_entity = Mock(return_value="stored-project")
    project = Mock()
    build_from_params = Mock(return_value=project)
    monkeypatch.setattr(base_crud_module.entity_factory, "build_entity_from_params", build_from_params)

    assert processor.create_project_entity_from_params(name="demo", kind="project") == "stored-project"

    build_from_params.assert_called_once_with(name="demo", kind="project")
    processor.create_project_entity.assert_called_once_with(project)


def _project_with_workflows(workflows: list[dict]) -> SimpleNamespace:
    return SimpleNamespace(name="demo", spec=SimpleNamespace(workflows=workflows))


def test_get_project_workflow_refreshes_and_reads_the_workflow_by_key() -> None:
    crud_processor = Mock()
    processor = ProjectProcessor(crud_processor)
    processor.refresh_project_entity = Mock()
    project = _project_with_workflows([{"name": "train", "key": "train-key"}, {"name": "main", "key": "main-key"}])

    result = processor.get_project_workflow(project, "train")

    assert result is crud_processor.read_context_entity.return_value
    processor.refresh_project_entity.assert_called_once_with(project)
    crud_processor.read_context_entity.assert_called_once_with("train-key", entity_type="workflow", project="demo")


def test_get_project_workflow_uses_main_by_default_and_matches_keys() -> None:
    crud_processor = Mock()
    processor = ProjectProcessor(crud_processor)
    processor.refresh_project_entity = Mock()

    processor.get_project_workflow(_project_with_workflows([{"name": "main", "key": "main-key"}]))
    processor.get_project_workflow(_project_with_workflows([{"name": "other", "key": "other-key"}]), "other-key")

    assert [call.args[0] for call in crud_processor.read_context_entity.call_args_list] == ["main-key", "other-key"]


def test_get_project_workflow_raises_when_the_workflow_is_missing() -> None:
    processor = ProjectProcessor(Mock())
    processor.refresh_project_entity = Mock()
    project = _project_with_workflows([])

    with pytest.raises(EntityError, match="Workflow missing not found"):
        processor.get_project_workflow(project, "missing")

    processor.refresh_project_entity.assert_called_once_with(project)
