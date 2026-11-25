# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import importlib
import inspect
from types import SimpleNamespace

import pytest

from digitalhub.entities.artifact.artifact import crud as artifact_kind_crud
from digitalhub.factory.crud import bind_project_shortcut
from digitalhub.factory.plugins import CrudPlugin, EntityPlugin
from digitalhub.factory.registry import BuilderRegistry
from digitalhub.utils.exceptions import BuilderError


class StubBuilder:
    ENTITY_KIND = "function:stub"


class OtherBuilder:
    ENTITY_KIND = "function:other"


class StubRuntimeBuilder:
    pass


def test_entity_plugin_registers_builder_and_resolves_shortcut(monkeypatch) -> None:
    def new_function_stub(project: str, name: str, image: str | None = None) -> tuple[str, str, str | None]:
        return project, name, image

    plugin = EntityPlugin(
        builder=StubBuilder,
        shortcuts=(CrudPlugin(new_function_stub),),
        runtime_builder=StubRuntimeBuilder,
    )
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["stub_runtime"])
    monkeypatch.setattr(
        registry_module,
        "import_module",
        lambda package: (
            SimpleNamespace(entity_plugins=(), generic_entity_builders=())
            if package == "digitalhub.entities.builders"
            else SimpleNamespace(entity_plugins=(plugin,))
            if package == "stub_runtime"
            else SimpleNamespace()
        ),
    )

    assert registry.get_entity_builder("function:stub").__class__ is StubBuilder
    assert registry.get_runtime_builder("function:stub").__class__ is StubRuntimeBuilder
    assert registry.get_shortcut_names() == ("new_function_stub",)

    resolved = registry.get_shortcut("new_function_stub")

    assert resolved is new_function_stub
    assert resolved(project="demo", name="hello", image="python:3.12") == (
        "demo",
        "hello",
        "python:3.12",
    )


def test_shortcut_collision_is_rejected(monkeypatch) -> None:
    def duplicate(project: str) -> str:
        return project

    plugin = EntityPlugin(
        builder=StubBuilder,
        shortcuts=(CrudPlugin(duplicate),),
    )
    second_plugin = EntityPlugin(
        builder=OtherBuilder,
        shortcuts=(CrudPlugin(duplicate),),
    )
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["one", "two"])
    modules = {
        "digitalhub.entities.builders": SimpleNamespace(entity_plugins=(), generic_entity_builders=()),
        "one": SimpleNamespace(entity_plugins=(plugin,)),
        "two": SimpleNamespace(entity_plugins=(second_plugin,)),
    }
    monkeypatch.setattr(registry_module, "import_module", lambda package: modules[package])

    with pytest.raises(BuilderError, match="Shortcut duplicate already exists"):
        registry.get_shortcut_names()


def test_core_shortcut_does_not_import_runtime_plugins(monkeypatch) -> None:
    def core_shortcut(project: str) -> str:
        return project

    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    core_module = SimpleNamespace(
        entity_plugins=(),
        generic_entity_builders=(),
        crud_plugins=(CrudPlugin(core_shortcut),),
    )

    def import_module(package: str):
        assert package == "digitalhub.entities.builders"
        return core_module

    def list_runtimes() -> list[str]:
        pytest.fail("Core shortcut lookup must not import runtime plugins.")

    monkeypatch.setattr(registry_module, "import_module", import_module)
    monkeypatch.setattr(registry_module, "list_runtimes", list_runtimes)

    assert registry.get_shortcut("core_shortcut") is core_shortcut
    assert registry.get_shortcut_spec("core_shortcut").function is core_shortcut


def test_project_shortcut_injects_project_and_preserves_signature() -> None:
    calls = []

    def shortcut(
        project: str,
        name: str,
        image: str | None = None,
    ) -> tuple[str, str, str | None]:
        calls.append((project, name, image))
        return project, name, image

    project = SimpleNamespace(name="demo", refresh=lambda: calls.append("refresh"))
    bound = bind_project_shortcut(shortcut, project, refresh_project=True)

    assert str(inspect.signature(bound)) == "(name: str, image: str | None = None) -> tuple[str, str, str | None]"
    assert bound("hello", image="python:3.12") == ("demo", "hello", "python:3.12")
    assert calls == [("demo", "hello", "python:3.12"), "refresh"]


def test_project_shortcut_forwards_variadic_keyword_arguments() -> None:
    def shortcut(project: str, name: str, **kwargs: object) -> tuple[str, str, dict[str, object]]:
        return project, name, kwargs

    project = SimpleNamespace(name="demo", refresh=lambda: None)
    bound = bind_project_shortcut(shortcut, project, refresh_project=False)

    assert bound("hello", handler="main") == ("demo", "hello", {"handler": "main"})
    assert bound("hello") == ("demo", "hello", {})


def test_project_shortcut_rejects_project_parameter() -> None:
    def shortcut(project: str, name: str) -> tuple[str, str]:
        return project, name

    project = SimpleNamespace(name="demo", refresh=lambda: None)
    bound = bind_project_shortcut(shortcut, project, refresh_project=False)

    with pytest.raises(TypeError):
        bound(project="other", name="hello")


def test_project_shortcut_injects_context() -> None:
    def shortcut(context: str, file: str) -> tuple[str, str]:
        return context, file

    project = SimpleNamespace(name="demo", refresh=lambda: None)
    bound = bind_project_shortcut(shortcut, project, refresh_project=False, inject_context=True)

    assert str(inspect.signature(bound)) == "(file: str) -> tuple[str, str]"
    assert "context" not in bound.__annotations__
    assert bound("entity.yaml") == ("demo", "entity.yaml")


def test_project_shortcut_keeps_context_without_injection() -> None:
    def shortcut(file: str, context: str | None = None) -> tuple[str, str | None]:
        return file, context

    project = SimpleNamespace(name="demo", refresh=lambda: None)
    bound = bind_project_shortcut(shortcut, project, refresh_project=False)

    assert str(inspect.signature(bound)) == "(file: str, context: str | None = None) -> tuple[str, str | None]"
    assert bound("entity.yaml", context="other") == ("entity.yaml", "other")


def test_project_update_shortcut_rejects_entities_from_other_projects() -> None:
    calls = []

    def update_function(entity: object) -> object:
        calls.append(entity)
        return entity

    project = SimpleNamespace(name="demo", refresh=lambda: None)
    bound = bind_project_shortcut(
        update_function,
        project,
        refresh_project=False,
        validate_entity_project=True,
    )

    with pytest.raises(ValueError, match="Entity to update is not in project demo"):
        bound(SimpleNamespace(project="other"))

    entity = SimpleNamespace(project="demo")
    assert bound(entity) is entity
    assert calls == [entity]


def test_digitalhub_module_resolves_shortcuts_and_lists_them(monkeypatch) -> None:
    digitalhub_module = importlib.import_module("digitalhub")
    shortcut = lambda project, name: (project, name)
    fake_registry = SimpleNamespace(
        get_shortcut=lambda name: shortcut,
        get_shortcut_names=lambda: ("new_function_stub",),
    )
    monkeypatch.setattr(digitalhub_module, "_registry", fake_registry)

    assert digitalhub_module.new_function_stub("demo", "hello") == ("demo", "hello")
    assert "new_function_stub" in dir(digitalhub_module)


def test_project_resolves_shortcut_and_lists_project_shortcuts(monkeypatch) -> None:
    project_module = importlib.import_module("digitalhub.entities.project._base.entity")
    project_class = project_module.Project
    project = project_class.__new__(project_class)
    refreshes = []
    object.__setattr__(project, "name", "demo")
    object.__setattr__(project, "refresh", lambda: refreshes.append("refresh"))

    def shortcut(project: str, name: str, image: str | None = None) -> tuple[str, str, str | None]:
        return project, name, image

    spec = CrudPlugin(shortcut)
    fake_registry = SimpleNamespace(
        get_shortcut_spec=lambda name: spec,
        get_shortcut=lambda name: shortcut,
        get_project_shortcut_names=lambda: ("new_function_stub",),
    )
    monkeypatch.setattr(project_module, "registry", fake_registry)

    bound = project.new_function_stub

    assert str(inspect.signature(bound)) == "(name: str, image: str | None = None) -> tuple[str, str, str | None]"
    assert bound("hello", image="python:3.12") == ("demo", "hello", "python:3.12")
    assert refreshes == ["refresh"]
    assert "new_function_stub" in dir(project)


def test_core_artifact_crud_plugins_are_discovered(monkeypatch) -> None:
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", list)

    assert {
        "new_artifact",
        "log_artifact",
        "log_generic_artifact",
        "register_artifact",
        "register_generic_artifact",
        "get_artifact",
        "get_artifact_versions",
        "list_artifacts",
        "import_artifact",
        "load_artifact",
        "update_artifact",
        "delete_artifact",
    }.issubset(registry.get_shortcut_names())
    assert registry.get_shortcut("log_artifact") is artifact_kind_crud.log_artifact


def test_generic_plugins_are_not_project_bound(monkeypatch) -> None:
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", list)

    shortcut_names = registry.get_shortcut_names()
    project_shortcut_names = registry.get_project_shortcut_names()

    generic_shortcut_names = {
        "log_generic_artifact",
        "log_generic_dataitem",
        "log_generic_model",
        "register_generic_artifact",
        "register_generic_dataitem",
        "register_generic_model",
    }
    assert generic_shortcut_names.issubset(shortcut_names)
    assert not generic_shortcut_names & set(project_shortcut_names)


def test_core_entity_crud_plugins_are_discovered(monkeypatch) -> None:
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", list)

    assert {
        "new_function",
        "get_function",
        "load_function",
        "new_dataitem",
        "log_table",
        "register_table",
        "new_model",
        "new_task",
        "new_run",
    }.issubset(registry.get_shortcut_names())


def test_core_read_shortcuts_do_not_refresh_project() -> None:
    entities_module = importlib.import_module("digitalhub.entities")
    read_plugins = [plugin for plugin in entities_module.crud_plugins if plugin.name.startswith(("get_", "list_"))]
    write_plugins = [plugin for plugin in entities_module.crud_plugins if plugin not in read_plugins]

    assert read_plugins
    assert all(not plugin.refresh_project for plugin in read_plugins)
    assert write_plugins
    assert all(plugin.refresh_project for plugin in write_plugins)


def test_hasattr_on_the_package_survives_a_broken_runtime(monkeypatch) -> None:
    import digitalhub

    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)

    def import_module(package: str):
        if package == "digitalhub_runtime_broken":
            raise RuntimeError("broken runtime")
        return importlib.import_module(package)

    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["digitalhub_runtime_broken"])
    monkeypatch.setattr(registry_module, "import_module", import_module)
    monkeypatch.setattr(digitalhub, "_registry", registry)

    assert not hasattr(digitalhub, "new_function_missing")
    assert digitalhub.new_artifact is registry.get_shortcut("new_artifact")
