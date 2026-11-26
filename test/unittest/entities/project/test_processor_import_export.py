# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.project._base.processor as processor_module
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.utils.exceptions import BackendError


def _processor_with_reordered_entity_types() -> ProjectProcessor:
    processor = ProjectProcessor(Mock())
    processor._get_entity_types = Mock(return_value=["functions", "artifacts"])
    processor._is_embedded = Mock(return_value=False)
    return processor


def _project_entities() -> dict:
    return {
        "spec": {
            "functions": [{"metadata": {"ref": "local://function.yaml"}}],
            "artifacts": [{"metadata": {"ref": "local://artifact.yaml"}}],
        }
    }


def test_import_entities_selects_processor_independently_of_entity_type_order(monkeypatch) -> None:
    processor = _processor_with_reordered_entity_types()
    monkeypatch.setattr(processor_module, "has_local_scheme", Mock(return_value=True))
    executable_import = Mock()
    monkeypatch.setattr(ContextEntityExecutableProcessor, "import_executable_entity", executable_import)

    processor._import_entities("project", _project_entities(), reset_id=True)

    processor.crud_processor.import_context_entity.assert_called_once_with(
        file="local://artifact.yaml", reset_id=True, context="project"
    )
    executable_import.assert_called_once_with(file="local://function.yaml", reset_id=True, context="project")


def test_import_embedded_entities_creates_them_with_singular_entity_types(monkeypatch) -> None:
    processor = ProjectProcessor(Mock())
    processor._is_embedded = Mock(return_value=True)
    entities = {
        "artifacts": [{"metadata": {}}],
        "dataitems": [{"metadata": {}}],
        "models": [{"metadata": {}}],
        "functions": [{"metadata": {}}],
        "workflows": [{"metadata": {}}],
    }
    built = Mock()
    build_entity = Mock(return_value=built)
    monkeypatch.setattr(processor_module.entity_factory, "build_entity_from_dict", build_entity)

    processor._import_entities("project", {"spec": entities})

    assert [call.kwargs["entity_type"] for call in build_entity.call_args_list] == [
        "artifact",
        "dataitem",
        "model",
        "function",
        "workflow",
    ]
    assert processor.crud_processor.create_context_entity.call_count == 5
    processor.crud_processor.create_context_entity.assert_called_with(built)
    built.save.assert_not_called()


def test_load_entities_selects_processor_independently_of_entity_type_order(monkeypatch) -> None:
    processor = _processor_with_reordered_entity_types()
    monkeypatch.setattr(processor_module, "has_local_scheme", Mock(return_value=True))
    executable_load = Mock()
    monkeypatch.setattr(ContextEntityExecutableProcessor, "load_executable_entity", executable_load)

    processor._load_entities(_project_entities())

    processor.crud_processor.load_context_entity.assert_called_once_with("local://artifact.yaml")
    executable_load.assert_called_once_with("local://function.yaml")


def _project(tmp_path) -> SimpleNamespace:
    return SimpleNamespace(name="project", ENTITY_TYPE="project", spec=SimpleNamespace(source=str(tmp_path)))


def test_export_writes_references_for_non_embedded_entities(monkeypatch, tmp_path) -> None:
    processor = ProjectProcessor(Mock())
    project = _project(tmp_path)
    processor._refresh_to_dict = Mock(return_value={"spec": {"artifacts": [{"key": "artifact-key", "metadata": {}}]}})
    artifact = SimpleNamespace(export=Mock(return_value="artifact.yaml"))
    processor.crud_processor.read_context_entity.return_value = artifact
    write_yaml = Mock()
    monkeypatch.setattr(processor_module, "write_yaml", write_yaml)

    result = processor.export_project_entity(project)

    expected_path = tmp_path / "projects-project.yaml"
    assert result == str(expected_path)
    processor._refresh_to_dict.assert_called_once_with(project)
    processor.crud_processor.read_context_entity.assert_called_once_with("artifact-key")
    artifact.export.assert_called_once_with()
    write_yaml.assert_called_once_with(
        expected_path,
        {"spec": {"artifacts": [{"key": "artifact-key", "metadata": {"ref": "artifact.yaml"}}]}},
    )


def test_export_skips_embedded_entities(monkeypatch, tmp_path) -> None:
    processor = ProjectProcessor(Mock())
    project = _project(tmp_path)
    embedded = {
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
    processor._refresh_to_dict = Mock(return_value=embedded)
    write_yaml = Mock()
    monkeypatch.setattr(processor_module, "write_yaml", write_yaml)

    processor.export_project_entity(project)

    processor.crud_processor.read_context_entity.assert_not_called()
    write_yaml.assert_called_once_with(tmp_path / "projects-project.yaml", embedded)


def test_refresh_to_dict_keeps_the_local_project_when_the_backend_fails() -> None:
    processor = ProjectProcessor(Mock())
    processor.refresh_project_entity = Mock(side_effect=BackendError("unreachable"))
    project = Mock()
    project.to_dict.return_value = {"name": "project"}

    assert processor._refresh_to_dict(project) == {"name": "project"}

    processor.refresh_project_entity.assert_called_once_with(project)
