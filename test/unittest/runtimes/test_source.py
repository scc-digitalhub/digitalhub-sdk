# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.source.source as source_module
from digitalhub.entities._mixin.source.source import fetch_source


@pytest.fixture
def fetch(monkeypatch) -> SimpleNamespace:
    """Fake git, http and S3; the downloads write an empty file."""

    def download(_source, filename) -> None:
        filename.write_bytes(b"")

    fakes = SimpleNamespace(
        clone=Mock(),
        download=Mock(side_effect=download),
        s3=Mock(side_effect=download),
        extract=Mock(),
    )
    monkeypatch.setattr(source_module, "clone_repository", fakes.clone)
    monkeypatch.setattr(source_module, "requests_chunk_download", fakes.download)
    monkeypatch.setattr(source_module, "get_store", Mock(return_value=SimpleNamespace(get_s3_source=fakes.s3)))
    monkeypatch.setattr(source_module, "extract_archive", fakes.extract)
    return fakes


def test_a_git_source_is_cloned(tmp_path, fetch) -> None:
    path = tmp_path / "src"

    fetch_source(path, "git+https://github.com/org/repo")

    assert path.is_dir()
    fetch.clone.assert_called_once_with(path, "git+https://github.com/org/repo")


def test_an_http_file_is_downloaded(tmp_path, fetch) -> None:
    fetch_source(tmp_path, "https://host/main.py")

    fetch.download.assert_called_once_with("https://host/main.py", tmp_path / "main.py")
    fetch.extract.assert_not_called()


@pytest.mark.parametrize(
    ("source", "downloader"),
    [("zip+https://host/src.zip", "download"), ("zip+s3://bucket/src.zip", "s3")],
)
def test_an_archive_is_extracted_and_removed(tmp_path, fetch, source, downloader) -> None:
    fetch_source(tmp_path, source)

    archive = tmp_path / "src.zip"
    expected = "https://host/src.zip" if downloader == "download" else source
    getattr(fetch, downloader).assert_called_once_with(expected, archive)
    fetch.extract.assert_called_once_with(tmp_path, archive)
    assert not archive.exists()


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("s3://bucket/main.py", "S3 source must be a zip file"),
        ("/local/main.py", "Unable to collect source from: /local/main.py"),
    ],
)
def test_other_sources_are_refused(tmp_path, fetch, source, message) -> None:
    with pytest.raises(RuntimeError, match=message):
        fetch_source(tmp_path, source)
