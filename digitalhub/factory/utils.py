# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib
from importlib.metadata import EntryPoint, entry_points
from types import ModuleType
from typing import Any

from digitalhub.factory.enums import FactoryEnum


def import_module(package: str) -> ModuleType:
    """
    Import a module dynamically by package name.

    Parameters
    ----------
    package : str
        The fully qualified package name to import.

    Returns
    -------
    ModuleType
        The imported module object.
    """
    try:
        return importlib.import_module(package)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Package {package} not found.") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred while importing {package}.") from e


def import_object(path: str) -> Any:
    """
    Import an object from a ``"package.module:attribute"`` path.

    Parameters
    ----------
    path : str
        Module path and attribute name separated by a colon.

    Returns
    -------
    Any
        The imported object.
    """
    module_name, _, attribute = path.partition(":")
    if not module_name or not attribute:
        raise ValueError(f"Invalid object path '{path}': expected 'package.module:attribute'.")
    module = importlib.import_module(module_name)
    try:
        return getattr(module, attribute)
    except AttributeError as e:
        raise ImportError(f"Module '{module_name}' has no attribute '{attribute}'.") from e


def list_runtime_entry_points() -> list[EntryPoint]:
    """
    List the installed runtime plugins.

    Each runtime declares, in the ``digitalhub.runtimes`` entry point group,
    the tuple of ``EntityPlugin`` it registers.

    Returns
    -------
    list[EntryPoint]
        Runtime entry points, sorted by name.
    """
    group = entry_points(group=FactoryEnum.RUNTIMES_ENTRY_POINT_GROUP.value)
    return sorted(group, key=lambda entry_point: entry_point.name)
