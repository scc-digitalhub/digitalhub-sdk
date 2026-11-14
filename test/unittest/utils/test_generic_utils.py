import stat
from unittest.mock import MagicMock, Mock
from zipfile import ZipFile, ZipInfo

import pytest
import requests

from digitalhub.utils.generic_utils import create_archive, extract_archive, requests_chunk_download


def test_create_archive_is_removed_after_context(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("data")

    with create_archive(source) as archive_path:
        assert archive_path.is_file()
        with ZipFile(archive_path) as archive:
            assert archive.read("file.txt") == b"data"
        temporary_directory = archive_path.parent

    assert not archive_path.exists()
    assert not temporary_directory.exists()


def test_extract_archive_extracts_files_within_destination(tmp_path) -> None:
    archive_path = tmp_path / "archive.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/file.txt", "content")

    destination = tmp_path / "destination"
    extract_archive(destination, archive_path)

    assert (destination / "nested/file.txt").read_text() == "content"


@pytest.mark.parametrize("member_name", ["../escaped.txt", "/outside.txt"])
def test_extract_archive_rejects_paths_outside_destination(
    tmp_path,
    member_name: str,
) -> None:
    archive_path = tmp_path / "archive.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(member_name, "content")

    with pytest.raises(ValueError, match="Unsafe path in archive"):
        extract_archive(tmp_path / "destination", archive_path)

    assert not (tmp_path / "escaped.txt").exists()


def test_extract_archive_rejects_symbolic_links(tmp_path) -> None:
    archive_path = tmp_path / "archive.zip"
    symlink = ZipInfo("link")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(symlink, "../../escaped.txt")

    with pytest.raises(ValueError, match="Unsafe symbolic link in archive"):
        extract_archive(tmp_path / "destination", archive_path)


@pytest.mark.parametrize(
    ("timeout", "expected_timeout"),
    [
        ((10, 60), (10, 60)),
        (5.0, 5.0),
        ((2.0, 5.0), (2.0, 5.0)),
    ],
)
def test_requests_chunk_download_uses_finite_configurable_timeout(
    monkeypatch,
    tmp_path,
    timeout,
    expected_timeout,
) -> None:
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"content"]
    get = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", get)

    destination = tmp_path / "download.bin"
    requests_chunk_download("https://example.test/download.bin", destination, timeout)

    assert destination.read_bytes() == b"content"
    get.assert_called_once_with(
        "https://example.test/download.bin",
        stream=True,
        timeout=expected_timeout,
    )
