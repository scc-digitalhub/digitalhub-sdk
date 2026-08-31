import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.entities.project._base.entity import Project


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


@pytest.mark.parametrize(
    ("method_name", "manager_name"),
    [
        ("load_artifact", "artifact"),
        ("load_dataitem", "dataitem"),
        ("load_model", "model"),
        ("load_function", "function"),
        ("load_workflow", "workflow"),
        ("load_task", "task"),
        ("load_run", "run"),
        ("load_trigger", "trigger"),
        ("load_secret", "secret"),
    ],
)
def test_load_entity_delegates_to_crud_manager(method_name: str, manager_name: str) -> None:
    loaded = object()
    manager = Mock()
    manager.load.return_value = loaded
    project = object.__new__(Project)
    project.crud = SimpleNamespace(**{manager_name: manager})
    project.refresh = Mock()

    result = getattr(project, method_name)("entity.yaml")

    assert result is loaded
    manager.load.assert_called_once_with("entity.yaml")
    project.refresh.assert_called_once_with()
