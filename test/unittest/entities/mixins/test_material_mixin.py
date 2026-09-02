from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.material.mixin as material_mixin
from digitalhub.entities._mixin.material.mixin import MaterialMixin
from digitalhub.utils.exceptions import BackendError, EntityError, EntityErrorFileNotFound


class MaterialEntityForTest(MaterialMixin):
    ENTITY_TYPE = "artifact"

    def __init__(self) -> None:
        self.project = "my-project"
        self.id = "entity-id"
        self.status = SimpleNamespace(files=None)
        self.save = Mock()
        self.refresh = Mock()


def test_init_material_extensions_defaults_to_empty_list() -> None:
    entity = MaterialEntityForTest()

    entity._init_material_extensions()

    assert entity.extensions == []


def test_as_file_downloads_to_store_temp_directory(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store._build_temp.return_value = "/tmp/material"
    store.download.return_value = ["/tmp/material/file.txt"]
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))

    result = entity.as_file()

    assert result == ["/tmp/material/file.txt"]
    store._build_temp.assert_called_once_with()
    store.download.assert_called_once_with("store://material", dst="/tmp/material")


@pytest.mark.parametrize(
    ("destination", "expected_destination"),
    [(None, Path("/context/artifact")), ("/tmp/download", Path("/tmp/download"))],
)
def test_download_uses_context_or_explicit_destination(
    destination: str | None,
    expected_destination: Path,
    monkeypatch,
) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    entity._context = Mock(return_value=SimpleNamespace(root=Path("/context")))
    store = Mock()
    store.download.return_value = "/downloaded"
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))

    result = entity.download(destination=destination, overwrite=True)

    assert result == "/downloaded"
    store.download.assert_called_once_with(
        "store://material",
        expected_destination,
        overwrite=True,
    )


def test_upload_sets_ready_state_and_logs_file_info(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store.upload.return_value = ["file.txt"]
    store.get_file_info.return_value = [{"path": "file.txt"}]
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))

    entity.upload("/source", keep_dir_structure=True)

    assert entity.status.state == "READY"
    assert entity.status.message is None
    assert entity.status.files == [{"path": "file.txt"}]
    assert entity.save.call_count == 2
    entity.save.assert_any_call(update=True)
    store.upload.assert_called_once_with(
        "/source",
        "store://material",
        keep_dir_structure=True,
    )
    store.get_file_info.assert_called_once_with("store://material", ["file.txt"])


def test_upload_stores_large_file_metadata_in_backend(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    files_info = [{"path": f"file-{index}"} for index in range(101)]
    store = Mock()
    store.upload.return_value = [file_info["path"] for file_info in files_info]
    store.get_file_info.return_value = files_info
    update_files_info = Mock()
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))
    monkeypatch.setattr(material_mixin.material_processor, "update_files_info", update_files_info)

    entity.upload("/source")

    assert entity.status.state == "READY"
    assert entity.status.files == []
    update_files_info.assert_called_once_with(
        "my-project",
        "artifact",
        "entity-id",
        files_info,
    )


def test_upload_converts_missing_source_to_entity_error(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store.upload.side_effect = FileNotFoundError("missing.txt")
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))

    with pytest.raises(EntityErrorFileNotFound, match="missing.txt"):
        entity.upload("/missing")

    assert entity.status.state == "ERROR"
    assert "Please verify" in entity.status.message
    assert entity.save.call_count == 2


def test_upload_converts_store_errors_to_entity_error(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store.upload.side_effect = ValueError("invalid source")
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))

    with pytest.raises(EntityError, match="invalid source"):
        entity.upload("/source")

    assert entity.status.state == "ERROR"
    assert entity.status.message == "Upload failed: invalid source"
    assert entity.save.call_count == 2


def test_files_reads_backend_info_and_falls_back_to_status(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.status.files = [{"path": "status.txt"}]
    read_files_info = Mock(return_value=[{"path": "backend.txt"}])
    monkeypatch.setattr(material_mixin.material_processor, "read_files_info", read_files_info)

    assert entity.files == [{"path": "backend.txt"}]
    read_files_info.assert_called_once_with(
        project="my-project",
        entity_type="artifact",
        entity_id="entity-id",
    )

    read_files_info.reset_mock()
    read_files_info.side_effect = BackendError("backend unavailable")

    assert entity.files == [{"path": "status.txt"}]
