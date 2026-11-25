# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from unittest.mock import Mock

import pytest

import digitalhub.context.api as context_api
import digitalhub.entities._processors.base.crud as base_crud_module
import digitalhub.entities.project._base.entity as project_entity_module
import digitalhub.stores.session as session_module
from digitalhub.context.api import get_context
from digitalhub.entities._processors.processors import base_crud_processor
from digitalhub.entities.project._base.entity import Project
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.session import Session
from digitalhub.utils.exceptions import ContextError


@pytest.fixture
def session(monkeypatch) -> Session:
    """Replace the process session with an empty one."""
    current = Session(transport=Mock(), identity=Mock())
    monkeypatch.setattr(session_module, "_session", current)
    return current


def _project_dict(source: Path) -> dict:
    return {"name": "demo", "kind": "project", "metadata": {}, "spec": {"source": str(source)}, "status": {}}


def _backend(monkeypatch, module, response) -> Mock:
    """Make the client resolved by ``module`` answer every request with ``response``."""
    client = Mock()
    client.execute.return_value = response
    client.execute_list.return_value = response
    monkeypatch.setattr(module, "resolve_client", Mock(return_value=client))
    return client


def test_building_a_project_neither_builds_a_client_nor_registers_a_context(session, monkeypatch, tmp_path) -> None:
    client = Mock(wraps=session.client)
    monkeypatch.setattr(session, "client", client)

    entity_factory.build_entity_from_dict(_project_dict(tmp_path))

    client.assert_not_called()
    with pytest.raises(ContextError):
        session.contexts.get("demo")


@pytest.mark.parametrize("operation", ["read", "update"])
def test_project_state_from_the_backend_registers_the_context(session, monkeypatch, tmp_path, operation) -> None:
    _backend(monkeypatch, base_crud_module, _project_dict(tmp_path / "backend"))

    if operation == "read":
        base_crud_processor.read_project_entity("project", "demo")
    else:
        base_crud_processor.update_project_entity("project", "demo", {})

    assert session.contexts.get("demo").root == tmp_path / "backend"


def test_creating_a_project_registers_the_context_the_backend_returns(session, tmp_path) -> None:
    project: Project = entity_factory.build_entity_from_dict(_project_dict(tmp_path / "local"))
    project._client = Mock()
    project._client.execute.return_value = _project_dict(tmp_path / "backend")

    base_crud_processor.create_project_entity(_entity=project)

    assert session.contexts.get("demo").root == tmp_path / "backend"


def test_listing_projects_registers_no_context(session, monkeypatch, tmp_path) -> None:
    _backend(monkeypatch, base_crud_module, [_project_dict(tmp_path)])

    assert [project.name for project in base_crud_processor.list_project_entities("project")] == ["demo"]
    with pytest.raises(ContextError):
        session.contexts.get("demo")


def test_a_project_built_from_a_file_does_not_move_the_registered_root(session, monkeypatch, tmp_path) -> None:
    # Building a project registered its context, so a listing or a YAML file
    # with another source changed where every entity of the project exported.
    _backend(monkeypatch, base_crud_module, _project_dict(tmp_path / "backend"))
    base_crud_processor.read_project_entity("project", "demo")

    entity_factory.build_entity_from_dict(_project_dict(tmp_path / "elsewhere"))

    assert session.contexts.get("demo").root == tmp_path / "backend"


def test_unknown_project_context_is_registered_from_the_backend(session, monkeypatch, tmp_path) -> None:
    _backend(monkeypatch, context_api, _project_dict(tmp_path / "backend"))

    context = get_context("demo")

    assert context.root == tmp_path / "backend"
    assert session.contexts.get("demo") is context


def test_import_registers_the_created_project_before_importing_its_entities(session, monkeypatch, tmp_path) -> None:
    _backend(monkeypatch, project_entity_module, _project_dict(tmp_path / "backend"))
    monkeypatch.setattr(base_crud_module, "read_yaml", Mock(return_value=_project_dict(tmp_path / "file")))
    roots_seen_by_import: list[Path] = []
    monkeypatch.setattr(
        Project,
        "_import_entities",
        lambda self, obj, reset_id=False: roots_seen_by_import.append(session.contexts.get("demo").root),
    )
    monkeypatch.setattr(Project, "refresh", lambda self: self)

    base_crud_processor.import_project_entity("project.yaml")

    assert roots_seen_by_import == [tmp_path / "backend"]
