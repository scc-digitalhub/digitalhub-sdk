from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.context.builder import ContextBuilder
from digitalhub.context.context import Context
from digitalhub.entities._commons.enums import Relationship
from digitalhub.entities.project._base.entity import Project
from digitalhub.runtimes.enums import RuntimeEnvVar
from digitalhub.utils.exceptions import ContextError


def test_project_context_io_is_lazy(monkeypatch, tmp_path) -> None:
    root = tmp_path / "non-existent-dir-xyz"
    client = Mock()
    builder = ContextBuilder()
    run = SimpleNamespace(key="run-key", id="run-id")

    monkeypatch.setattr("digitalhub.entities.project._base.entity.get_client", Mock(return_value=client))
    monkeypatch.setattr("digitalhub.entities.project._base.entity.build_context", builder.build)
    monkeypatch.setattr(
        "digitalhub.context.context.entity_factory.build_entity_from_dict",
        Mock(return_value=run),
    )
    monkeypatch.setenv(RuntimeEnvVar.RUN_ID.value, "run-123")

    project = Project(
        name="project",
        kind="project",
        metadata=SimpleNamespace(),
        spec=SimpleNamespace(source=str(root), config={}),
        status=SimpleNamespace(),
    )
    context = builder.get(project.name)

    assert not root.exists()
    client.execute.assert_not_called()

    assert context.is_running
    client.execute.assert_called_once()
    assert context.run is run
    client.execute.assert_called_once()

    monkeypatch.setattr(project, "_refresh_to_dict", Mock(return_value={"spec": {}}))
    monkeypatch.setattr(project, "_get_entity_types", Mock(return_value=[]))
    project.export()

    assert root.is_dir()
    assert (root / "projects-project.yaml").is_file()


def test_register_entity_requires_an_active_run() -> None:
    context = object.__new__(Context)
    context.run = None
    context.logged = {}
    entity = Mock()

    with pytest.raises(ContextError, match="active run"):
        context.register_entity(entity)

    entity.add_relationship.assert_not_called()
    assert context.logged == {}


def test_register_entity_records_producer_relationship() -> None:
    context = object.__new__(Context)
    context.run = SimpleNamespace(key="run-key", id="run-id")
    context.logged = {}
    entity = Mock(name="artifact")
    entity.name = "artifact"
    entity.key = "artifact-key"

    assert context.register_entity(entity) is entity

    entity.add_relationship.assert_called_once_with(Relationship.PRODUCEDBY.value, "run-key:run-id")
    assert context.logged == {"artifact": "artifact-key"}
