# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from digitalhub.utils.logger.logger import get_logger

logger = get_logger(__file__)

# Version specifiers, in the order they are looked for.
SEPARATORS = ("==", ">=", "<=", ">", "<", "~=", "!=")


def parse_requirements(requirements: list[str] | str | None) -> list[str] | None:
    """
    Parse the requirements of an executable.

    A string is the path of a requirements file. A requirement without a
    version takes the version installed in the local environment, if any.

    Parameters
    ----------
    requirements : list[str] | str | None
        Requirements, or the path of a requirements.txt, pyproject.toml,
        conda.yaml or conda.yml file.

    Returns
    -------
    list[str] | None
        Requirements, or None if none are given.
    """
    if requirements is None:
        return None
    if isinstance(requirements, str):
        requirements = _read_requirements_file(requirements)
    return _pin_to_installed(requirements)


def _read_requirements_file(path: str) -> list[str]:
    """Read the requirements from a file, by its name."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"Requirements file not found: {path}")
    if not file.is_file():
        raise ValueError(f"Provided path is not a file: {path}")
    reader = _READERS.get(file.name)
    if reader is None:
        raise ValueError(f"Unsupported requirements file: {file.name}. Supported filenames are: {', '.join(_READERS)}.")
    return reader(path)


def _read_pip(path: str) -> list[str]:
    """Read a requirements file with the parser of pip."""
    from pip._internal.network.session import PipSession
    from pip._internal.req import parse_requirements as pip_parse

    return [str(req.requirement) for req in pip_parse(path, session=PipSession()) if req.requirement]


def _read_pyproject(path: str) -> list[str]:
    """Read the dependencies of the project from a pyproject.toml."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    with open(path, "rb") as f:
        dependencies = tomllib.load(f).get("project", {}).get("dependencies", [])
    return list(dependencies) if isinstance(dependencies, list) else []


def _read_conda(path: str) -> list[str]:
    """Read the pip dependencies from a conda environment file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    requirements: list[str] = []
    if not data or "dependencies" not in data:
        return requirements
    for dependency in data["dependencies"]:
        if isinstance(dependency, dict) and "pip" in dependency:
            requirements.extend(dependency["pip"])
    return requirements


_READERS = {
    "requirements.txt": _read_pip,
    "pyproject.toml": _read_pyproject,
    "conda.yaml": _read_conda,
    "conda.yml": _read_conda,
}


def _installed_packages() -> list[str]:
    """Packages installed in the local environment, as pip freeze lists them."""
    from pip._internal.operations import freeze

    return list(freeze.freeze())


def _pin_to_installed(requirements: list[str]) -> list[str]:
    """Give the requirements without a version the version installed locally."""
    installed: dict[str, str] = {}
    for package in _installed_packages():
        for separator in SEPARATORS:
            if separator in package:
                name, version = package.split(separator, 1)
                installed[name.lower().replace("_", "-")] = f"{name}{separator}{version}"
                break

    pinned = []
    for requirement in requirements:
        installed_requirement = None
        if not any(separator in requirement for separator in SEPARATORS):
            installed_requirement = installed.get(requirement.lower().replace("_", "-"))
        if installed_requirement is None:
            pinned.append(requirement)
            continue
        logger.warning(
            f"Warning: {requirement} version unspecified, using version {installed_requirement} inferred "
            "from local environment. To override set an explicit version."
        )
        pinned.append(installed_requirement)
    return pinned
