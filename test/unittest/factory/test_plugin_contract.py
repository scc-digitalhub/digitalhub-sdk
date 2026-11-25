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

ALL_BUILDERS = ("FakeFunctionBuilder", "FakeTaskBuilder", "FakeRunBuilder")
ALL_KINDS = ("fake", "fake+job", "fake+job:run")

BUILDERS = """\
from digitalhub.plugins import FunctionBuilder, RunBuilder, RuntimeEntityBuilder, TaskBuilder, map_actions


class Family(RuntimeEntityBuilder):
    EXECUTABLE_KIND = "fake"
    TASKS_KINDS = map_actions([("fake+job", "job")])
    RUN_KINDS = map_actions([("fake+job:run", "job")])


class FakeFunctionBuilder(FunctionBuilder, Family):
    ENTITY_KIND = "fake"


class FakeTaskBuilder(TaskBuilder, Family):
    ENTITY_KIND = "fake+job"


class FakeRunBuilder(RunBuilder, Family):
    ENTITY_KIND = "fake+job:run"
"""

RUNTIME = """\
from digitalhub.plugins import RuntimeBuilder


class Builder(RuntimeBuilder):
    pass
"""

ORPHAN = """\
from digitalhub.plugins import FunctionBuilder


class OrphanBuilder(FunctionBuilder):
    ENTITY_KIND = "fake-orphan"
"""

MakePackage = Callable[..., str]


@pytest.fixture
def make_package(tmp_path: Path, monkeypatch) -> MakePackage:
    """Write and install a runtime package that registers ``builders``; return its name."""
    monkeypatch.syspath_prepend(str(tmp_path))
    created: list[str] = []

    def make(
        builders: tuple[str, ...] = ALL_BUILDERS,
        runtime_builder: str = "runtimes:Builder",
        extra: dict[str, str] | None = None,
        entry_point: bool = True,
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
                "from digitalhub.plugins import EntityPlugin\n"
                f"from {name}.entities.builders import FakeFunctionBuilder, FakeRunBuilder, FakeTaskBuilder\n\n"
                f"entity_plugins = (\n{plugins})\n"
            ),
            **(extra or {}),
        }
        if entry_point:
            # What ``pip install`` writes for an entry point declared in pyproject.toml.
            dist_info = tmp_path / f"{name}-0.0.0.dist-info"
            dist_info.mkdir()
            (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: 0.0.0\n")
            (dist_info / "entry_points.txt").write_text(f"[digitalhub.runtimes]\nfake = {name}:entity_plugins\n")
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
    package = make_package(builders=("FakeFunctionBuilder", "FakeTaskBuilder"))

    with pytest.raises(AssertionError) as error:
        check_plugin_package(package)

    message = str(error.value)
    assert "family 'fake': kind 'fake+job:run' is not registered by a builder of the family" in message
    assert "builder FakeRunBuilder for kind 'fake+job:run' is not registered" in message


def test_an_unavailable_runtime_builder_is_reported(make_package: MakePackage) -> None:
    package = make_package(runtime_builder="missing:Builder")

    with pytest.raises(
        AssertionError, match=r"runtime builder '.*missing:Builder' \(kinds fake, .*\) cannot be imported"
    ):
        check_plugin_package(package, kinds=ALL_KINDS)


EXECUTION_ONLY_RUNTIME = """\
import missing_execution_dependency

from digitalhub.plugins import RuntimeBuilder


class Builder(RuntimeBuilder):
    pass
"""


def test_a_runtime_builder_needing_an_execution_dependency_is_checked_statically(make_package: MakePackage) -> None:
    # dbt imports psycopg2, installed only where its runs execute.
    package = make_package(extra={"runtimes.py": EXECUTION_ONLY_RUNTIME})

    check_plugin_package(package, kinds=ALL_KINDS)


def test_a_wrong_runtime_builder_path_is_reported_even_without_its_dependencies(make_package: MakePackage) -> None:
    package = make_package(runtime_builder="runtimes:Misspelled", extra={"runtimes.py": EXECUTION_ONLY_RUNTIME})

    with pytest.raises(AssertionError, match="Misspelled.* cannot be imported"):
        check_plugin_package(package, kinds=ALL_KINDS)


def test_imports_from_private_core_modules_are_reported(make_package: MakePackage) -> None:
    package = make_package(
        extra={
            "utils.py": (
                "import typing\n\n"
                "if typing.TYPE_CHECKING:\n"
                "    from digitalhub.entities._base.entity.spec import Spec\n"
                "from digitalhub.utils.logger.logger import get_logger\n"
            )
        }
    )

    with pytest.raises(AssertionError) as error:
        check_plugin_package(package, kinds=ALL_KINDS)

    message = str(error.value)
    assert f"{package}/utils.py:4 imports the private core module 'digitalhub.entities._base.entity.spec'" in message
    assert "digitalhub.utils.logger" not in message


def test_a_package_without_entry_point_is_reported(make_package: MakePackage) -> None:
    package = make_package(entry_point=False)

    with pytest.raises(AssertionError, match="no entry point in the 'digitalhub.runtimes' group"):
        check_plugin_package(package, kinds=ALL_KINDS)
