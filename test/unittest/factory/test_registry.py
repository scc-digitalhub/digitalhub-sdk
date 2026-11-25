# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import importlib
import threading
from collections.abc import Callable
from types import SimpleNamespace

import pytest

from digitalhub.factory.plugins import EntityPlugin
from digitalhub.factory.registry import BuilderRegistry
from digitalhub.utils.exceptions import BuilderError


class StubBuilder:
    pass


class CoreEntityStubBuilder:
    ENTITY_KIND = "core-entity"


class RuntimeEntityStubBuilder:
    ENTITY_KIND = "runtime-entity"


class BrokenBuilder:
    def __init__(self) -> None:
        raise RuntimeError("broken builder")


def test_core_registration_rolls_back_partial_state_and_can_retry(monkeypatch) -> None:
    registry = BuilderRegistry()
    failing_module = SimpleNamespace(
        entity_plugins=(EntityPlugin(builder=CoreEntityStubBuilder),),
        generic_entity_builders=(("generic", BrokenBuilder),),
    )
    successful_module = SimpleNamespace(
        entity_plugins=(EntityPlugin(builder=CoreEntityStubBuilder),),
        generic_entity_builders=(("generic", StubBuilder),),
    )
    modules = iter((failing_module, successful_module))
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "import_module", lambda _: next(modules))

    with pytest.raises(BuilderError, match="Failed to register core entities"):
        registry._ensure_entities_registered()

    assert registry._entity_builders == {}
    assert registry._generic_entity_builders == {}

    registry._ensure_entities_registered()

    assert set(registry._entity_builders) == {"core-entity"}
    assert set(registry._generic_entity_builders) == {"generic"}


def test_runtime_registration_rolls_back_partial_state_and_can_retry(monkeypatch) -> None:
    registry = BuilderRegistry()
    runtime_module = SimpleNamespace(
        entity_plugins=(EntityPlugin(builder=RuntimeEntityStubBuilder, runtime_builder=StubBuilder),),
    )
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["runtime-one", "runtime-two"])
    fail_second_import = True

    def import_runtime(package: str):
        if package == "runtime-two" and fail_second_import:
            raise RuntimeError("broken runtime")
        return runtime_module if package == "runtime-one" else SimpleNamespace(entity_plugins=())

    monkeypatch.setattr(registry_module, "import_module", import_runtime)

    with pytest.raises(BuilderError, match="Failed to register runtime entities"):
        registry._ensure_runtimes_registered()

    assert registry._entity_builders == {}
    assert registry._runtime_builders == {}

    fail_second_import = False
    registry._ensure_runtimes_registered()

    assert set(registry._entity_builders) == {"runtime-entity"}
    assert set(registry._runtime_builders) == {"runtime-entity"}


def test_runtime_registration_rejects_legacy_builder_exports(monkeypatch) -> None:
    registry = BuilderRegistry()
    legacy_module = SimpleNamespace(
        entity_builders=(("runtime-entity", RuntimeEntityStubBuilder),),
        runtime_builders=(("runtime-entity", StubBuilder),),
    )
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["legacy-runtime"])
    monkeypatch.setattr(registry_module, "import_module", lambda _: legacy_module)

    with pytest.raises(BuilderError, match="does not define 'entity_plugins'"):
        registry._ensure_runtimes_registered()

    assert registry._entity_builders == {}
    assert registry._runtime_builders == {}


# Time a competing thread is given to overtake a paused registration. With the
# lock it stays blocked, so this only bounds the test; it never decides it.
OVERTAKE_WINDOW = 0.5
JOIN_TIMEOUT = 5


def _install_fake_plugins(monkeypatch, calls: list[str] | None = None) -> BuilderRegistry:
    """Return a fresh registry wired to one core kind and one runtime kind."""
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    modules = {
        "digitalhub.entities.builders": SimpleNamespace(
            entity_plugins=(EntityPlugin(builder=CoreEntityStubBuilder),),
            generic_entity_builders=(),
        ),
        "fake_runtime": SimpleNamespace(
            entity_plugins=(EntityPlugin(builder=RuntimeEntityStubBuilder, runtime_builder=StubBuilder),),
        ),
    }

    def import_module(package: str):
        if calls is not None:
            calls.append(package)
        return modules[package]

    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["fake_runtime"])
    monkeypatch.setattr(registry_module, "import_module", import_module)
    return registry


def _pause_first_registration(monkeypatch, registry: BuilderRegistry) -> tuple[threading.Event, threading.Event]:
    """
    Pause the first registration pass after it has copied the registry state.

    Returns the event set once the pass is paused and the event that resumes it.
    """
    paused = threading.Event()
    resume = threading.Event()
    original = registry._register_entity_plugins

    def register_entity_plugins(*args) -> None:
        if not paused.is_set():
            paused.set()
            resume.wait(JOIN_TIMEOUT)
        original(*args)

    monkeypatch.setattr(registry, "_register_entity_plugins", register_entity_plugins)
    return paused, resume


def _start(target: Callable[[], object], errors: list[BaseException]) -> tuple[threading.Thread, threading.Event]:
    done = threading.Event()

    def run() -> None:
        try:
            target()
        except BaseException as e:  # noqa: BLE001 - surfaced by the test
            errors.append(e)
        finally:
            done.set()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, done


def test_concurrent_registration_does_not_lose_runtime_builders(monkeypatch) -> None:
    # Thread B copies the empty state and pauses; thread A then registers core
    # and runtime kinds. Without a lock B's stale copy overwrites A's work while
    # both flags end up True, so the runtime kind stays unresolvable forever.
    registry = _install_fake_plugins(monkeypatch)
    paused, resume = _pause_first_registration(monkeypatch, registry)
    errors: list[BaseException] = []

    thread_b, _ = _start(lambda: registry.get_entity_builder("core-entity"), errors)
    assert paused.wait(JOIN_TIMEOUT)

    thread_a, a_done = _start(lambda: registry.get_entity_builder("runtime-entity"), errors)
    a_done.wait(OVERTAKE_WINDOW)
    resume.set()

    for thread in (thread_a, thread_b):
        thread.join(JOIN_TIMEOUT)
        assert not thread.is_alive()
    assert errors == []
    assert registry.get_entity_builder("core-entity").__class__ is CoreEntityStubBuilder
    assert registry.get_entity_builder("runtime-entity").__class__ is RuntimeEntityStubBuilder
    assert registry.get_runtime_builder("runtime-entity").__class__ is StubBuilder


def test_concurrent_registration_runs_each_phase_once(monkeypatch) -> None:
    calls: list[str] = []
    registry = _install_fake_plugins(monkeypatch, calls)
    paused, resume = _pause_first_registration(monkeypatch, registry)
    errors: list[BaseException] = []

    first, _ = _start(registry.get_shortcut_names, errors)
    assert paused.wait(JOIN_TIMEOUT)

    others = [_start(registry.get_shortcut_names, errors) for _ in range(7)]
    for _, done in others:
        done.wait(OVERTAKE_WINDOW / len(others))
    resume.set()

    for thread in [first, *(thread for thread, _ in others)]:
        thread.join(JOIN_TIMEOUT)
        assert not thread.is_alive()
    assert errors == []
    assert calls == ["digitalhub.entities.builders", "fake_runtime"]


def test_core_registration_requires_entity_plugins(monkeypatch) -> None:
    registry = BuilderRegistry()
    legacy_core = SimpleNamespace(entity_builders=(("core-entity", CoreEntityStubBuilder),), generic_entity_builders=())
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "import_module", lambda _: legacy_core)

    with pytest.raises(BuilderError, match="Failed to register core entities"):
        registry._ensure_entities_registered()


def _registry_with_runtime_plugin(monkeypatch, plugin: EntityPlugin) -> BuilderRegistry:
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    modules = {
        "digitalhub.entities.builders": SimpleNamespace(entity_plugins=(), generic_entity_builders=()),
        "fake_runtime": SimpleNamespace(entity_plugins=(plugin,)),
    }
    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["fake_runtime"])
    monkeypatch.setattr(registry_module, "import_module", lambda package: modules[package])
    return registry


def test_runtime_builder_path_is_imported_on_first_use(monkeypatch) -> None:
    imported: list[str] = []
    registry_module = importlib.import_module(BuilderRegistry.__module__)

    def import_object(path: str):
        imported.append(path)
        return StubBuilder

    monkeypatch.setattr(registry_module, "import_object", import_object)
    registry = _registry_with_runtime_plugin(
        monkeypatch,
        EntityPlugin(builder=RuntimeEntityStubBuilder, runtime_builder="fake_runtime.runtimes:Builder"),
    )

    assert registry.get_entity_builder("runtime-entity").__class__ is RuntimeEntityStubBuilder
    assert imported == []

    first = registry.get_runtime_builder("runtime-entity")

    assert first.__class__ is StubBuilder
    assert registry.get_runtime_builder("runtime-entity") is first
    assert imported == ["fake_runtime.runtimes:Builder"]


def test_unavailable_runtime_builder_reports_its_cause(monkeypatch) -> None:
    # Runtimes used to swallow this ImportError and register no runtime, so
    # local execution failed with "not found" and no trace of the real cause.
    registry = _registry_with_runtime_plugin(
        monkeypatch,
        EntityPlugin(builder=RuntimeEntityStubBuilder, runtime_builder="missing_runtime_module_xyz:Builder"),
    )

    assert registry.get_entity_builder("runtime-entity").__class__ is RuntimeEntityStubBuilder
    with pytest.raises(BuilderError, match="'runtime-entity' is not available: No module named") as error:
        registry.get_runtime_builder("runtime-entity")

    assert isinstance(error.value.__cause__, ModuleNotFoundError)


def test_shortcut_lookup_raises_only_attribute_errors(monkeypatch) -> None:
    registry = BuilderRegistry()
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    discovered: list[str] = []

    def import_module(package: str):
        discovered.append(package)
        if package == "broken_runtime":
            raise RuntimeError("broken runtime")
        return SimpleNamespace(entity_plugins=(), generic_entity_builders=())

    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["broken_runtime"])
    monkeypatch.setattr(registry_module, "import_module", import_module)

    with pytest.raises(AttributeError):
        registry.get_shortcut_spec("__wrapped__")
    assert discovered == []

    with pytest.raises(AttributeError, match="plugin discovery failed") as error:
        registry.get_shortcut_spec("new_function_python")

    assert isinstance(error.value.__cause__, BuilderError)
