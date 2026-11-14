from zipfile import ZipFile

from digitalhub.utils.generic_utils import create_archive


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
