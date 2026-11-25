# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import itertools
import sys
from collections.abc import Callable
from enum import Enum
from pathlib import Path

import pytest
from plugin_contract import check_plugin_package

_package_ids = itertools.count()

ALL_BUILDERS = ("FunctionBuilder", "TaskBuilder", "RunBuilder")
ALL_KINDS = ("fake", "fake+job", "fake+job:run")

BUILDERS = """\
from digitalhub.entities._base.entity.builder import EntityBuilder
from digitalhub.entities._commons.utils import map_actions
from digitalhub.entities._mixin.runtime_entity.builder import RuntimeEntityBuilder


class Family(RuntimeEntityBuilder):
    EXECUTABLE_KIND = "fake"
    TASKS_KINDS = map_actions([("fake+job", "job")])
    RUN_KINDS = map_actions([("fake+job:run", "job")])


class FunctionBuilder(EntityBuilder, Family):
    ENTITY_TYPE = "function"
    ENTITY_KIND = "fake"


class TaskBuilder(EntityBuilder, Family):
    ENTITY_TYPE = "task"
    ENTITY_KIND = "fake+job"


class RunBuilder(EntityBuilder, Family):
    ENTITY_TYPE = "run"
    ENTITY_KIND = "fake+job:run"
"""

RUNTIME = """\
from digitalhub.runtimes.builder import RuntimeBuilder


class Builder(RuntimeBuilder):
    pass
"""

ORPHAN = """\
from digitalhub.entities._base.entity.builder import EntityBuilder


class OrphanBuilder(EntityBuilder):
    ENTITY_TYPE = "function"
    ENTITY_KIND = "fake-orphan"
"""

MakePackage = Callable[..., str]


@pytest.fixture
def make_package(tmp_path: Path, monkeypatch) -> MakePackage:
    """Write a runtime package that registers ``builders`` and return its name."""
    monkeypatch.syspath_prepend(str(tmp_path))
    created: list[str] = []

    def make(
        builders: tuple[str, ...] = ALL_BUILDERS,
        runtime_builder: str = "runtimes:Builder",
        extra: dict[str, str] | None = None,
    ) -> str:
        name = f"fake_runtime_{next(_package_ids)}"
        created.append(name)
        plugins = "".join(
            f"    EntityPlugin(builder={builder}, runtime_builder='{name}.{runtime_builder}'),\n"
            for builder in builders
        )
        sources = {
            "__init__.py": f"from {name}.entities import entity_plugins\n",
            "runtimes.py": RUNTIME,
            "entities/builders.py": BUILDERS,
            "entities/__init__.py": (
                "from digitalhub.factory.plugins import EntityPlugin\n"
                f"from {name}.entities.builders import FunctionBuilder, RunBuilder, TaskBuilder\n\n"
                f"entity_plugins = (\n{plugins})\n"
            ),
            **(extra or {}),
        }
        for path, source in sources.items():
            target = tmp_path / name / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
        return name

    yield make
    for module in [module for module in sys.modules if module.startswith(tuple(created))]:
        del sys.modules[module]


def test_a_complete_package_passes(make_package: MakePackage) -> None:
    check_plugin_package(make_package(), kinds=ALL_KINDS)


def test_kinds_can_be_an_enum(make_package: MakePackage) -> None:
    kinds = Enum("EntityKinds", {"FUNCTION": "fake", "TASK": "fake+job", "RUN": "fake+job:run"})

    check_plugin_package(make_package(), kinds=kinds)


def test_modules_outside_entities_are_not_imported(make_package: MakePackage) -> None:
    # Runtimes keep optional execution dependencies outside ``entities``.
    package = make_package(extra={"dsl.py": "import missing_execution_dependency\n"})

    check_plugin_package(package, kinds=ALL_KINDS)


def test_drift_between_declared_and_registered_kinds_is_reported(make_package: MakePackage) -> None:
    # modelserve had builders nobody registered, kinds without builders and a
    # builder module that could not even be imported: no test noticed.
    package = make_package(
        extra={
            "entities/orphan.py": ORPHAN,
            "entities/broken.py": "from nowhere import missing_name\n",
        }
    )

    with pytest.raises(AssertionError) as error:
        check_plugin_package(package, kinds=(*ALL_KINDS, "fake-missing"))

    message = str(error.value)
    assert f"module '{package}.entities.broken' cannot be imported" in message
    assert "builder OrphanBuilder for kind 'fake-orphan' is not registered" in message
    assert "kind 'fake-missing' has no registered builder" in message


def test_an_incomplete_family_is_reported(make_package: MakePackage) -> None:
    package = make_package(builders=("FunctionBuilder", "TaskBuilder"))

    with pytest.raises(AssertionError) as error:
        check_plugin_package(package)

    message = str(error.value)
    assert "family 'fake': kind 'fake+job:run' is not registered by a builder of the family" in message
    assert "builder RunBuilder for kind 'fake+job:run' is not registered" in message


def test_an_unavailable_runtime_builder_is_reported(make_package: MakePackage) -> None:
    package = make_package(runtime_builder="missing:Builder")

    with pytest.raises(AssertionError, match="runtime builder of kind 'fake' cannot be imported"):
        check_plugin_package(package, kinds=ALL_KINDS)
