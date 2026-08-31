import importlib
from types import SimpleNamespace

import pytest

from digitalhub.factory.registry import BuilderRegistry
from digitalhub.utils.exceptions import BuilderError


class StubBuilder:
    pass


class BrokenBuilder:
    def __init__(self) -> None:
        raise RuntimeError("broken builder")


def test_core_registration_rolls_back_partial_state_and_can_retry(monkeypatch) -> None:
    registry = BuilderRegistry()
    failing_module = SimpleNamespace(
        entity_builders=(("entity", StubBuilder),),
        generic_entity_builders=(("generic", BrokenBuilder),),
    )
    successful_module = SimpleNamespace(
        entity_builders=(("entity", StubBuilder),),
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

    assert set(registry._entity_builders) == {"entity"}
    assert set(registry._generic_entity_builders) == {"generic"}


def test_runtime_registration_rolls_back_partial_state_and_can_retry(monkeypatch) -> None:
    registry = BuilderRegistry()
    runtime_module = SimpleNamespace(
        entity_builders=(("runtime-entity", StubBuilder),),
        runtime_builders=(("runtime", StubBuilder),),
    )
    registry_module = importlib.import_module(BuilderRegistry.__module__)
    monkeypatch.setattr(registry_module, "list_runtimes", lambda: ["runtime-one", "runtime-two"])
    fail_second_import = True

    def import_runtime(package: str):
        if package == "runtime-two" and fail_second_import:
            raise RuntimeError("broken runtime")
        return runtime_module if package == "runtime-one" else SimpleNamespace()

    monkeypatch.setattr(registry_module, "import_module", import_runtime)

    with pytest.raises(BuilderError, match="Failed to register runtime entities"):
        registry._ensure_runtimes_registered()

    assert registry._entity_builders == {}
    assert registry._runtime_builders == {}

    fail_second_import = False
    registry._ensure_runtimes_registered()

    assert set(registry._entity_builders) == {"runtime-entity"}
    assert set(registry._runtime_builders) == {"runtime"}
