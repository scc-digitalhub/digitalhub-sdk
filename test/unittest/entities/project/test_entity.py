# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import inspect
from unittest.mock import Mock

import pytest

from digitalhub.entities.artifact import crud as artifact_crud
from digitalhub.entities.artifact.artifact import crud as artifact_kind_crud
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.project._base.processor import ProjectProcessor


def _project_for_shortcuts() -> Project:
    project = object.__new__(Project)
    object.__setattr__(project, "name", "project")
    object.__setattr__(project, "refresh", Mock())
    return project


def test_project_resolves_artifact_crud_plugins_dynamically() -> None:
    project = _project_for_shortcuts()

    log_artifact = project.log_artifact
    get_artifact = project.get_artifact
    load_artifact = project.load_artifact
    import_artifact = project.import_artifact

    assert log_artifact.__wrapped__ is artifact_kind_crud.log_artifact
    assert get_artifact.__wrapped__ is artifact_crud.get_artifact
    assert load_artifact.__wrapped__ is artifact_crud.load_artifact
    assert import_artifact.__wrapped__ is artifact_crud.import_artifact
    assert "project" not in inspect.signature(log_artifact).parameters
    assert "project" not in inspect.signature(get_artifact).parameters
    assert "context" not in inspect.signature(import_artifact).parameters
    assert "file" in inspect.signature(load_artifact).parameters


@pytest.mark.parametrize(
    ("property_name", "shortcut_name"),
    [
        ("functions", "list_functions"),
        ("workflows", "list_workflows"),
        ("artifacts", "list_artifacts"),
        ("dataitems", "list_dataitems"),
        ("models", "list_models"),
    ],
)
def test_project_entity_properties_use_dynamic_list_shortcuts(property_name: str, shortcut_name: str) -> None:
    project = object.__new__(Project)
    listed = object()
    shortcut = Mock(return_value=listed)
    object.__setattr__(project, shortcut_name, shortcut)

    assert getattr(project, property_name) is listed
    shortcut.assert_called_once_with()


@pytest.mark.parametrize(
    ("call", "processor_method"),
    [
        (lambda project: project.save(), "create_project_entity"),
        (lambda project: project.save(update=True), "update_project_entity"),
        (lambda project: project.update(), "update_project_entity"),
        (lambda project: project.refresh(), "refresh_project_entity"),
    ],
)
def test_persistence_delegates_to_the_project_processor(monkeypatch, call, processor_method) -> None:
    project = object.__new__(Project)
    method = Mock(side_effect=lambda project: project)
    monkeypatch.setattr(ProjectProcessor, processor_method, method)

    assert call(project) is project

    method.assert_called_once_with(project)


def test_search_entity_delegates_to_search_processor(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    search = Mock(return_value=([], []))
    monkeypatch.setattr(ProjectProcessor, "search_entity", search)

    result = project.search_entity(
        query="query",
        entity_types=["artifacts"],
        name="artifact",
        kind="artifact",
        created="created",
        updated="updated",
        description="description",
        labels=["label"],
        custom="value",
    )

    assert result == ([], [])
    search.assert_called_once_with(
        "project",
        query="query",
        entity_types=["artifacts"],
        name="artifact",
        kind="artifact",
        created="created",
        updated="updated",
        description="description",
        labels=["label"],
        custom="value",
    )


def test_run_runs_the_workflow_the_processor_finds(monkeypatch) -> None:
    project = object.__new__(Project)
    workflow = Mock()
    workflow.run.return_value = "run"
    get_workflow = Mock(return_value=workflow)
    monkeypatch.setattr(ProjectProcessor, "get_project_workflow", get_workflow)

    assert project.run(workflow="main", action="pipeline", parameter="value") == "run"

    get_workflow.assert_called_once_with(project, "main")
    workflow.run.assert_called_once_with(action="pipeline", parameter="value")


def test_export_delegates_to_the_project_processor(monkeypatch) -> None:
    project = object.__new__(Project)
    export = Mock(return_value="projects-project.yaml")
    monkeypatch.setattr(ProjectProcessor, "export_project_entity", export)

    assert project.export() == "projects-project.yaml"

    export.assert_called_once_with(project)
