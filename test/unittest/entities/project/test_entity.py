# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import importlib
import inspect
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.entities.artifact import crud as artifact_crud
from digitalhub.entities.artifact.artifact import crud as artifact_kind_crud
from digitalhub.entities.project._base.entity import Project
from digitalhub.utils.exceptions import EntityError


def _project_with_reordered_entity_types() -> Project:
    project = object.__new__(Project)
    project.name = "project"
    project._get_entity_types = Mock(return_value=["functions", "artifacts"])
    project._is_embedded = Mock(return_value=False)
    return project


def _project_entities() -> dict:
    return {
        "spec": {
            "functions": [{"metadata": {"ref": "local://function.yaml"}}],
            "artifacts": [{"metadata": {"ref": "local://artifact.yaml"}}],
        }
    }


def test_import_entities_selects_processor_independently_of_entity_type_order(monkeypatch) -> None:
    project = _project_with_reordered_entity_types()
    method_module = importlib.import_module(Project._import_entities.__module__)
    monkeypatch.setattr(method_module, "has_local_scheme", Mock(return_value=True))
    context_import = Mock()
    executable_import = Mock()
    monkeypatch.setattr(method_module.crud_processor, "import_context_entity", context_import)
    monkeypatch.setattr(method_module.executable_processor, "import_executable_entity", executable_import)

    project._import_entities(_project_entities(), reset_id=True)

    context_import.assert_called_once_with(file="local://artifact.yaml", reset_id=True, context="project")
    executable_import.assert_called_once_with(file="local://function.yaml", reset_id=True, context="project")


def test_load_entities_selects_processor_independently_of_entity_type_order(monkeypatch) -> None:
    project = _project_with_reordered_entity_types()
    method_module = importlib.import_module(Project._load_entities.__module__)
    monkeypatch.setattr(method_module, "has_local_scheme", Mock(return_value=True))
    context_load = Mock()
    executable_load = Mock()
    monkeypatch.setattr(method_module.crud_processor, "load_context_entity", context_load)
    monkeypatch.setattr(method_module.executable_processor, "load_executable_entity", executable_load)

    project._load_entities(_project_entities())

    context_load.assert_called_once_with("local://artifact.yaml")
    executable_load.assert_called_once_with("local://function.yaml")


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


def test_save_creates_project_and_updates_attributes(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    created = object()
    create_project = Mock(return_value=created)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_crud_processor.create_project_entity",
        create_project,
    )
    project._update_attributes = Mock()

    result = project.save()

    assert result is project
    create_project.assert_called_once_with(_entity=project)
    project._update_attributes.assert_called_once_with(created)


def test_save_updates_project(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    project.to_dict = Mock(return_value={"name": "project"})
    updated = object()
    update_project = Mock(return_value=updated)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_crud_processor.update_project_entity",
        update_project,
    )
    project._update_attributes = Mock()

    result = project.save(update=True)

    assert result is project
    update_project.assert_called_once_with(
        entity_type=project.ENTITY_TYPE,
        entity_name="project",
        entity_dict={"name": "project"},
    )
    project._update_attributes.assert_called_once_with(updated)


def test_refresh_reads_project_and_updates_attributes(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    refreshed = object()
    read_project = Mock(return_value=refreshed)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_crud_processor.read_project_entity",
        read_project,
    )
    project._update_attributes = Mock()

    result = project.refresh()

    assert result is project
    read_project.assert_called_once_with(entity_type=project.ENTITY_TYPE, entity_name="project")
    project._update_attributes.assert_called_once_with(refreshed)


def test_export_writes_references_for_non_embedded_entities(monkeypatch, tmp_path) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    project.spec = SimpleNamespace(source=str(tmp_path))
    project._refresh_to_dict = Mock(return_value={"spec": {"artifacts": [{"key": "artifact-key", "metadata": {}}]}})
    artifact = SimpleNamespace(export=Mock(return_value="artifact.yaml"))
    read_entity = Mock(return_value=artifact)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.crud_processor.read_context_entity",
        read_entity,
    )
    write_yaml = Mock()
    monkeypatch.setattr("digitalhub.entities.project._base.entity.write_yaml", write_yaml)

    result = project.export()

    expected_path = tmp_path / "projects-project.yaml"
    assert result == str(expected_path)
    project._refresh_to_dict.assert_called_once_with()
    read_entity.assert_called_once_with("artifact-key")
    artifact.export.assert_called_once_with()
    write_yaml.assert_called_once_with(
        expected_path,
        {"spec": {"artifacts": [{"key": "artifact-key", "metadata": {"ref": "artifact.yaml"}}]}},
    )


def test_export_skips_embedded_entities(monkeypatch, tmp_path) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    project.spec = SimpleNamespace(source=str(tmp_path))
    project._refresh_to_dict = Mock(
        return_value={
            "spec": {
                "artifacts": [
                    {
                        "key": "artifact-key",
                        "metadata": {"embedded": True},
                        "spec": {"path": "artifact.bin"},
                    }
                ]
            }
        }
    )
    read_entity = Mock()
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.crud_processor.read_context_entity",
        read_entity,
    )
    write_yaml = Mock()
    monkeypatch.setattr("digitalhub.entities.project._base.entity.write_yaml", write_yaml)

    project.export()

    read_entity.assert_not_called()
    write_yaml.assert_called_once_with(
        tmp_path / "projects-project.yaml",
        {
            "spec": {
                "artifacts": [
                    {
                        "key": "artifact-key",
                        "metadata": {"embedded": True},
                        "spec": {"path": "artifact.bin"},
                    }
                ]
            }
        },
    )


def test_search_entity_delegates_to_search_processor(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    search = Mock(return_value=([], []))
    monkeypatch.setattr("digitalhub.entities.project._base.entity.search_processor.search_entity", search)

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


def test_run_refreshes_selects_workflow_and_forwards_kwargs() -> None:
    project = object.__new__(Project)
    project.spec = SimpleNamespace(workflows=[{"name": "main", "key": "workflow-key"}])
    project.refresh = Mock()
    workflow = Mock()
    workflow.run.return_value = "run"
    project.get_workflow = Mock(return_value=workflow)

    result = project.run(workflow="main", parameter="value")

    assert result == "run"
    project.refresh.assert_called_once_with()
    project.get_workflow.assert_called_once_with("workflow-key")
    workflow.run.assert_called_once_with(parameter="value")


def test_run_uses_main_workflow_by_default() -> None:
    project = object.__new__(Project)
    project.spec = SimpleNamespace(workflows=[{"name": "main", "key": "workflow-key"}])
    project.refresh = Mock()
    workflow = Mock()
    project.get_workflow = Mock(return_value=workflow)

    project.run()

    project.get_workflow.assert_called_once_with("workflow-key")
    workflow.run.assert_called_once_with()


def test_run_raises_when_workflow_is_not_found() -> None:
    project = object.__new__(Project)
    project.spec = SimpleNamespace(workflows=[])
    project.refresh = Mock()

    with pytest.raises(EntityError, match="Workflow missing not found"):
        project.run(workflow="missing")

    project.refresh.assert_called_once_with()
