# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
Contract check that runtime packages run in their own test suites.

Runtimes import it as ``plugin_contract`` with this folder on ``PYTHONPATH``,
as they already do for ``validate_entities``.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterable
from enum import Enum
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
    - a runtime builder cannot be imported or is not a ``RuntimeBuilder``.

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
    _check_runtime_builders(plugins, problems)

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


def _check_runtime_builders(plugins: tuple[EntityPlugin, ...], problems: list[str]) -> None:
    for plugin in plugins:
        runtime_builder = plugin.runtime_builder
        if runtime_builder is None:
            continue
        try:
            builder = import_object(runtime_builder) if isinstance(runtime_builder, str) else runtime_builder
        except Exception as e:  # noqa: BLE001 - reported as a contract problem
            problems.append(f"runtime builder of kind '{plugin.kind}' cannot be imported: {e!r}")
            continue
        if not (isinstance(builder, type) and issubclass(builder, RuntimeBuilder)):
            problems.append(f"runtime builder of kind '{plugin.kind}' is not a RuntimeBuilder: {builder!r}")
