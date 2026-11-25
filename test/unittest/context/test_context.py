import contextvars
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.context.api as context_api
from digitalhub.context.builder import ContextBuilder
from digitalhub.context.context import Context
from digitalhub.entities._commons.enums import Relationship
from digitalhub.entities.project._base.entity import Project
from digitalhub.runtimes.enums import RuntimeEnvVar
from digitalhub.utils.exceptions import ContextError


def _context() -> Context:
    project = SimpleNamespace(
        name="project",
        spec=SimpleNamespace(config={}, source="."),
    )
    return Context(project)


def test_get_default_store_uses_project_configuration(monkeypatch) -> None:
    config = {"default_files_store": "s3://project-store"}
    context = SimpleNamespace(config=config)
    get_default_store_uri = Mock(return_value="s3://project-store")
    get_context = Mock(return_value=context)
    monkeypatch.setattr(context_api, "get_context", get_context)
    monkeypatch.setattr(context_api, "get_default_store_uri", get_default_store_uri)

    assert context_api.get_default_store("project") == "s3://project-store"
    get_context.assert_called_once_with("project")
    get_default_store_uri.assert_called_once_with(config)


def test_project_context_io_is_lazy(monkeypatch, tmp_path) -> None:
    root = tmp_path / "non-existent-dir-xyz"
    client = Mock()
    builder = ContextBuilder()
    run = SimpleNamespace(key="run-key", id="run-id")

    monkeypatch.setattr("digitalhub.context.context.resolve_client", Mock(return_value=client))
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
    context = _context()
    context.run = None
    context.logged = {}
    entity = Mock()

    with pytest.raises(ContextError, match="active run"):
        context.register_entity(entity)

    entity.add_relationship.assert_not_called()
    assert context.logged == {}


def test_register_entity_records_producer_relationship() -> None:
    context = _context()
    context.run = SimpleNamespace(key="run-key", id="run-id")
    context.logged = {}
    entity = Mock(name="artifact")
    entity.name = "artifact"
    entity.key = "artifact-key"

    assert context.register_entity(entity) is entity

    entity.add_relationship.assert_called_once_with(Relationship.PRODUCEDBY.value, "run-key:run-id")
    assert context.logged == {"artifact": "artifact-key"}


def test_active_run_and_logged_entities_are_isolated_by_contextvars_context(monkeypatch) -> None:
    context = _context()
    monkeypatch.delenv(RuntimeEnvVar.RUN_ID.value, raising=False)
    first_run = SimpleNamespace(key="run-key", id="run-1")
    second_run = SimpleNamespace(key="run-key", id="run-2")

    def register(run: SimpleNamespace, name: str) -> None:
        context.set_run(run)
        entity = Mock()
        entity.name = name
        entity.key = f"{name}-key"
        context.register_entity(entity)

    first_context = contextvars.Context()
    second_context = contextvars.Context()
    first_context.run(register, first_run, "first")
    second_context.run(register, second_run, "second")

    assert first_context.run(lambda: (context.run, context.is_running, dict(context.logged))) == (
        first_run,
        True,
        {"first": "first-key"},
    )
    assert second_context.run(lambda: (context.run, context.is_running, dict(context.logged))) == (
        second_run,
        True,
        {"second": "second-key"},
    )

    first_context.run(context.unset_run)

    assert first_context.run(lambda: (context.run, context.is_running, dict(context.logged))) == (
        None,
        False,
        {},
    )
    assert second_context.run(lambda: context.run) is second_run


def test_context_run_id_fallback_is_restored_after_local_run(monkeypatch) -> None:
    context = _context()
    backend_run = SimpleNamespace(key="run-key", id="backend-run")
    local_run = SimpleNamespace(key="run-key", id="local-run")
    get_run = Mock(return_value=backend_run)
    monkeypatch.setattr(context, "_get_run", get_run)
    monkeypatch.setenv(RuntimeEnvVar.RUN_ID.value, "backend-run")

    assert context.run is backend_run
    assert context.is_running
    context.logged["fallback-entry"] = "value"

    context.set_run(local_run)
    context.logged["local-entry"] = "value"
    assert context.run is local_run

    context.unset_run()
    assert context.run is backend_run
    assert context.is_running
    assert context.logged == {"fallback-entry": "value"}
    get_run.assert_called_once_with("backend-run")


def test_local_run_before_fallback_read_disables_late_run_id_lookup(monkeypatch) -> None:
    context = _context()
    local_run = SimpleNamespace(key="run-key", id="local-run")
    get_run = Mock()
    monkeypatch.setattr(context, "_get_run", get_run)
    monkeypatch.setenv(RuntimeEnvVar.RUN_ID.value, "backend-run")

    context.set_run(local_run)
    context.unset_run()

    assert context.run is None
    assert not context.is_running
    get_run.assert_not_called()


def test_unset_before_fallback_read_disables_late_run_id_lookup(monkeypatch) -> None:
    context = _context()
    get_run = Mock()
    monkeypatch.setattr(context, "_get_run", get_run)
    monkeypatch.setenv(RuntimeEnvVar.RUN_ID.value, "backend-run")

    context.unset_run()

    assert context.run is None
    assert not context.is_running
    get_run.assert_not_called()


def test_run_state_uses_one_context_variable_for_all_contexts(monkeypatch) -> None:
    # One ContextVar per Context accumulated in every execution context that
    # set a run, since contextvars.Context keeps its variables alive.
    monkeypatch.delenv(RuntimeEnvVar.RUN_ID.value, raising=False)
    run = SimpleNamespace(key="run-key", id="run-id")

    def exercise() -> int:
        for _ in range(5):
            context = _context()
            context.set_run(run)
            context.unset_run()
        return len(contextvars.copy_context())

    assert contextvars.Context().run(exercise) <= 1


def test_rebuilt_context_does_not_inherit_local_run(monkeypatch) -> None:
    monkeypatch.delenv(RuntimeEnvVar.RUN_ID.value, raising=False)
    run = SimpleNamespace(key="run-key", id="run-id")

    def exercise() -> tuple:
        previous = _context()
        previous.set_run(run)
        rebuilt = _context()
        return previous.run, rebuilt.run, rebuilt.is_running

    assert contextvars.Context().run(exercise) == (run, None, False)
