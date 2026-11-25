# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
Contract check that runtime packages run in their own test suites.

Runtimes import it as ``plugin_contract`` with this folder on ``PYTHONPATH``,
as they already do for ``validate_entities``.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import pkgutil
from collections.abc import Iterable
from enum import Enum
from importlib.metadata import entry_points
from pathlib import Path
from types import ModuleType

from digitalhub.entities._base.entity.builder import EntityBuilder
from digitalhub.entities._mixin.runtime_entity.builder import RuntimeEntityBuilder
from digitalhub.factory.enums import FactoryEnum
from digitalhub.factory.plugins import EntityPlugin
from digitalhub.factory.utils import import_object
from digitalhub.runtimes.builder import RuntimeBuilder


def check_plugin_package(
    package: str | ModuleType,
    kinds: type[Enum] | Iterable[str] | None = None,
) -> None:
    """
    Check that a runtime package registers everything it declares.

    Every problem found is reported, in one ``AssertionError``:

    - a module of the ``entities`` subpackage cannot be imported;
    - an entity builder defined there is not registered by any plugin, or two
      plugins register the same kind;
    - a value of ``kinds`` has no registered builder, or a registered kind is
      missing from ``kinds``;
    - the executable, task and run kinds of a family are not all registered by
      builders of that family, the members declare different topologies, or an
      action has a task kind but no run kind;
    - a runtime builder cannot be imported or is not a ``RuntimeBuilder``; when
      only an execution dependency is missing (``psycopg2`` for ``dbt``), its
      module must still define the class;
    - a module of the package imports a private core module
      (``digitalhub.<...>._<...>``) instead of ``digitalhub.plugins``;
    - no entry point in the ``digitalhub.runtimes`` group loads the package's
      ``entity_plugins``, so the core would not find the runtime.

    Builders are looked up in the ``entities`` subpackage, where runtimes keep
    them, so modules that need optional execution dependencies are not
    imported; a package without that subpackage is scanned whole.

    Parameters
    ----------
    package : str | ModuleType
        The runtime package, the one exporting ``entity_plugins``.
    kinds : type[Enum] | Iterable[str] | None
        Every kind the package declares, for example its ``EntityKinds`` enum.

    Raises
    ------
    AssertionError
        If the package breaks the contract.
    """
    module = importlib.import_module(package) if isinstance(package, str) else package
    problems: list[str] = []

    plugins: tuple[EntityPlugin, ...] = tuple(getattr(module, FactoryEnum.REG_ENTITY_PLUGINS_VAR.value, ()))
    if not plugins:
        problems.append("the package exports no entity_plugins")
    registered = _registered_builders(plugins, problems)

    _check_package_builders(module, registered, problems)
    if kinds is not None:
        _check_kinds(kinds, registered, problems)
    _check_families(registered, problems)
    _check_runtime_builders(module, plugins, problems)
    _check_private_imports(module, problems)
    _check_entry_point(module, plugins, problems)

    if problems:
        details = "\n- ".join(problems)
        raise AssertionError(f"Plugin package '{module.__name__}' breaks the plugin contract:\n- {details}")


def _registered_builders(plugins: tuple[EntityPlugin, ...], problems: list[str]) -> dict[str, type]:
    registered: dict[str, type] = {}
    for plugin in plugins:
        if plugin.kind in registered:
            problems.append(f"kind '{plugin.kind}' is registered twice")
        registered[plugin.kind] = plugin.builder
    return registered


def _builder_modules(module: ModuleType, problems: list[str]) -> list[ModuleType]:
    if not hasattr(module, "__path__"):
        return [module]
    try:
        module = importlib.import_module(f"{module.__name__}.entities")
    except ModuleNotFoundError as e:
        if e.name != f"{module.__name__}.entities":
            raise
    modules = [module]
    names = [
        info.name
        for info in pkgutil.walk_packages(
            module.__path__,
            prefix=f"{module.__name__}.",
            onerror=lambda name: problems.append(f"package '{name}' cannot be imported"),
        )
    ]
    for name in names:
        try:
            modules.append(importlib.import_module(name))
        except Exception as e:  # noqa: BLE001 - reported as a contract problem
            problems.append(f"module '{name}' cannot be imported: {e!r}")
    return modules


def _check_package_builders(module: ModuleType, registered: dict[str, type], problems: list[str]) -> None:
    for package_module in _builder_modules(module, problems):
        for _, cls in inspect.getmembers(package_module, inspect.isclass):
            if cls.__module__ != package_module.__name__ or not issubclass(cls, EntityBuilder):
                continue
            if cls.ENTITY_KIND is not None and registered.get(cls.ENTITY_KIND) is not cls:
                problems.append(f"builder {cls.__qualname__} for kind '{cls.ENTITY_KIND}' is not registered")


def _check_kinds(kinds: type[Enum] | Iterable[str], registered: dict[str, type], problems: list[str]) -> None:
    declared = {member.value for member in kinds} if isinstance(kinds, type) and issubclass(kinds, Enum) else set(kinds)
    problems.extend(f"kind '{kind}' has no registered builder" for kind in sorted(declared - set(registered)))
    problems.extend(f"registered kind '{kind}' is not declared" for kind in sorted(set(registered) - declared))


def _topology(builder: type[RuntimeEntityBuilder]) -> tuple:
    return (builder.EXECUTABLE_KIND, tuple(builder.TASKS_KINDS or ()), tuple(builder.RUN_KINDS or ()))


def _check_families(registered: dict[str, type], problems: list[str]) -> None:
    families: dict[str, dict[str, type[RuntimeEntityBuilder]]] = {}
    for kind, builder in registered.items():
        if issubclass(builder, RuntimeEntityBuilder):
            families.setdefault(builder.EXECUTABLE_KIND, {})[kind] = builder

    for executable_kind, members in families.items():
        reference = next(iter(members.values()))
        executable, tasks, runs = _topology(reference)
        family_kinds = {executable, *(task.kind for task in tasks), *(run.kind for run in runs)}
        prefix = f"family '{executable_kind}'"

        for kind, builder in members.items():
            if _topology(builder) != _topology(reference):
                problems.append(
                    f"{prefix}: {builder.__qualname__} declares another topology than {reference.__qualname__}"
                )
            if kind not in family_kinds:
                problems.append(f"{prefix}: kind '{kind}' is not part of the family topology")
        for kind in sorted(family_kinds - set(members)):
            problems.append(f"{prefix}: kind '{kind}' is not registered by a builder of the family")
        for action in sorted({task.action for task in tasks} - {run.action for run in runs}):
            problems.append(f"{prefix}: action '{action}' has a task kind but no run kind")


def _check_runtime_builders(module: ModuleType, plugins: tuple[EntityPlugin, ...], problems: list[str]) -> None:
    kinds_by_builder: dict[object, list[str]] = {}
    for plugin in plugins:
        if plugin.runtime_builder is not None:
            kinds_by_builder.setdefault(plugin.runtime_builder, []).append(plugin.kind)

    package = module.__name__.split(".")[0]
    for runtime_builder, kinds in kinds_by_builder.items():
        subject = f"runtime builder {runtime_builder!r} (kinds {', '.join(kinds)})"
        if not isinstance(runtime_builder, str):
            builder = runtime_builder
        else:
            try:
                builder = import_object(runtime_builder)
            except ModuleNotFoundError as e:
                # A dependency installed only where runs execute, such as
                # psycopg2 for dbt: the path itself must still be right.
                missing = (e.name or "").split(".")[0]
                if missing in (package, "digitalhub") or not _defines(runtime_builder):
                    problems.append(f"{subject} cannot be imported: {e!r}")
                continue
            except Exception as e:  # noqa: BLE001 - reported as a contract problem
                problems.append(f"{subject} cannot be imported: {e!r}")
                continue
        if not (isinstance(builder, type) and issubclass(builder, RuntimeBuilder)):
            problems.append(f"{subject} is not a RuntimeBuilder")


def _defines(path: str) -> bool:
    """Return whether the module of ``"module:Class"`` defines the class, without importing it."""
    module_name, _, attribute = path.partition(":")
    try:
        spec = importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return False
    if spec is None or spec.origin is None:
        return False
    tree = ast.parse(Path(spec.origin).read_text())
    return any(isinstance(node, ast.ClassDef) and node.name == attribute for node in tree.body)


def _check_private_imports(module: ModuleType, problems: list[str]) -> None:
    paths = getattr(module, "__path__", None) or [str(Path(module.__file__).parent)]
    for root in paths:
        for path in sorted(Path(root).rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported = [node.module]
                elif isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                else:
                    continue
                for name in imported:
                    parts = name.split(".")
                    if parts[0] == "digitalhub" and any(part.startswith("_") for part in parts[1:]):
                        location = f"{path.relative_to(Path(root).parent)}:{node.lineno}"
                        problems.append(f"{location} imports the private core module '{name}'; use digitalhub.plugins")


def _check_entry_point(module: ModuleType, plugins: tuple[EntityPlugin, ...], problems: list[str]) -> None:
    group = FactoryEnum.RUNTIMES_ENTRY_POINT_GROUP.value
    for entry_point in entry_points(group=group):
        if entry_point.module.split(".")[0] != module.__name__.split(".")[0]:
            continue
        try:
            loaded = entry_point.load()
        except Exception as e:  # noqa: BLE001 - reported as a contract problem
            problems.append(f"entry point '{entry_point.name}' ({entry_point.value}) cannot be loaded: {e!r}")
            continue
        if plugins and isinstance(loaded, (tuple, list)) and tuple(loaded) == plugins:
            return
    problems.append(
        f"no entry point in the '{group}' group loads the package's entity_plugins: declare it in pyproject.toml "
        "and reinstall the package"
    )
