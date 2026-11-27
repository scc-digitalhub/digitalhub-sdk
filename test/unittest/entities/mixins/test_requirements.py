# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import textwrap
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.source.requirements as requirements_module
from digitalhub.entities._mixin.source.requirements import parse_requirements


@pytest.fixture
def installed(monkeypatch) -> Mock:
    """The local environment has pandas and scikit-learn; warnings are recorded."""
    monkeypatch.setattr(
        requirements_module,
        "_installed_packages",
        lambda: ["pandas==2.0.0", "scikit_learn==1.5.0", "editable @ file:///src"],
    )
    warning = Mock()
    monkeypatch.setattr(requirements_module.logger, "warning", warning)
    return warning


def test_no_requirements() -> None:
    assert parse_requirements(None) is None


def test_requirements_without_a_version_take_the_installed_one(installed) -> None:
    parsed = parse_requirements(["pandas", "Scikit-Learn", "numpy>=1", "torch"])

    assert parsed == ["pandas==2.0.0", "scikit_learn==1.5.0", "numpy>=1", "torch"]
    assert installed.call_count == 2


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("requirements.txt", "pandas\nnumpy>=1  # comment\n"),
        ("pyproject.toml", '[project]\ndependencies = ["pandas", "numpy>=1"]\n'),
        ("conda.yml", "dependencies:\n  - python=3.12\n  - pip:\n    - pandas\n    - numpy>=1\n"),
    ],
)
def test_requirements_files_are_read_by_name(tmp_path, installed, name, content) -> None:
    path = tmp_path / name
    path.write_text(content)

    assert parse_requirements(str(path)) == ["pandas==2.0.0", "numpy>=1"]


@pytest.mark.parametrize(
    ("name", "error", "message"),
    [
        ("missing.txt", FileNotFoundError, "Requirements file not found"),
        ("folder", ValueError, "Provided path is not a file"),
        ("reqs.txt", ValueError, "Unsupported requirements file: reqs.txt. Supported filenames are: requirements.txt,"),
        # Read as a requirements.txt, it gave the lines of the Python file.
        ("setup.py", ValueError, "Unsupported requirements file: setup.py"),
    ],
)
def test_other_paths_are_refused(tmp_path, name, error, message) -> None:
    (tmp_path / "folder").mkdir()
    (tmp_path / "reqs.txt").write_text("pandas\n")
    (tmp_path / "setup.py").write_text("from setuptools import setup\n")

    with pytest.raises(error, match=message):
        parse_requirements(str(tmp_path / name))


def test_a_requirements_txt_is_read_as_pip_does(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(requirements_module, "_installed_packages", list)
    monkeypatch.setenv("TORCH_VERSION", "2.5")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "base.txt").write_text("base-pkg\n-r nested.txt\n")
    (tmp_path / "sub" / "nested.txt").write_text("nested-pkg\n")
    path = tmp_path / "requirements.txt"
    path.write_text(
        "# comment\n"
        "numpy>=1  # comment\n"
        "-r sub/base.txt\n"
        "--index-url https://example.org/simple\n"
        "hashed==1.0 --hash=sha256:abc\n"
        "long \\\n"
        "    >=2\n"
        "torch==${TORCH_VERSION}\n"
        "-e ./local\n"
        "pkg @ git+https://github.com/org/repo.git\n"
    )

    assert parse_requirements(str(path)) == [
        "numpy>=1",
        "base-pkg",
        "nested-pkg",
        "hashed==1.0",
        "long     >=2",
        "torch==2.5",
        "./local",
        "pkg @ git+https://github.com/org/repo.git",
    ]


def test_requirements_are_parsed_without_pip(tmp_path) -> None:
    # pip has no public API: its internals changed under the SDK.
    path = tmp_path / "requirements.txt"
    path.write_text("pandas\n")
    script = textwrap.dedent(
        f"""
        import sys

        from digitalhub.plugins import parse_requirements

        parse_requirements({str(path)!r})
        loaded = [name for name in sys.modules if name == "pip" or name.startswith("pip.")]
        assert not loaded, f"Unexpected pip modules: {{loaded}}"
        """
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, check=False, text=True)

    assert result.returncode == 0, result.stderr
