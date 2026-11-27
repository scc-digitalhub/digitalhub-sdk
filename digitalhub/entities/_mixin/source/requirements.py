# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.metadata
import os
import re
import shlex
import sys
from pathlib import Path

import yaml

from digitalhub.utils.logger.logger import get_logger

logger = get_logger(__file__)

# Version specifiers, in the order they are looked for.
SEPARATORS = ("==", ">=", "<=", ">", "<", "~=", "!=")

# As pip reads a requirements file.
_COMMENT = re.compile(r"(^|\s+)#.*$")
_ENV_VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")
_FILE_OPTIONS = (("-r", "--requirement"), ("-c", "--constraint"), ("-e", "--editable"))


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
    """
    Read a requirements.txt as pip does.

    The files given with ``-r`` and ``-c`` are read too, relative to the
    file, and ``-e`` gives its target; the other options are skipped.
    """
    requirements = []
    for line in _logical_lines(Path(path).read_text()):
        # Options start at the first token with a dash, as in pip.
        tokens = line.split(" ")
        start = next((i for i, token in enumerate(tokens) if token.startswith("-")), len(tokens))
        if requirement := " ".join(tokens[:start]):
            requirements.append(requirement)
            continue
        option, value = _file_option(" ".join(tokens[start:]))
        if option == "-e":
            requirements.append(value)
        elif option is not None:
            requirements.extend(_read_pip(os.path.join(os.path.dirname(path), value)))
    return requirements


def _logical_lines(content: str) -> list[str]:
    """Lines of a requirements file: continuations joined, comments removed, ``${VAR}`` expanded."""
    joined: list[str] = []
    lines = []
    for line in content.splitlines():
        if line.endswith("\\") and not _COMMENT.match(line):
            joined.append(line.strip("\\"))
            continue
        if _COMMENT.match(line):
            line = " " + line
        lines.append("".join([*joined, line]))
        joined = []
    if joined:
        lines.append("".join(joined))
    stripped = (_COMMENT.sub("", line).strip() for line in lines)
    return [_ENV_VAR.sub(lambda m: os.getenv(m[1]) or m[0], line) for line in stripped if line]


def _file_option(options: str) -> tuple[str | None, str]:
    """The first ``-r``, ``-c`` or ``-e`` of a line of options, with its value."""
    tokens = shlex.split(options)
    for i, token in enumerate(tokens):
        for short, long in _FILE_OPTIONS:
            if token in (short, long) and i + 1 < len(tokens):
                return short, tokens[i + 1]
            if token.startswith(f"{long}="):
                return short, token.removeprefix(f"{long}=")
            if token.startswith(short) and not token.startswith("--") and len(token) > len(short):
                return short, token.removeprefix(short)
    return None, ""


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
    """
    Packages installed in the local environment, as ``name==version``.

    As pip freeze: the first installation of a package along ``sys.path``,
    and none of those installed from a URL or editable.
    """
    seen = set()
    packages = []
    for entry in sys.path:
        for dist in importlib.metadata.distributions(path=[entry]):
            name = dist.metadata["Name"]
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            if dist.read_text("direct_url.json") is None:
                packages.append(f"{name}=={dist.version}")
    return packages


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
