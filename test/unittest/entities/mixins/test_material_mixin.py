# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.material.files as material_files
import digitalhub.entities._mixin.material.mixin as material_mixin
import digitalhub.entities._processors.context.material as context_material
from digitalhub.entities._mixin.material.mixin import MaterialMixin
from digitalhub.utils.exceptions import BackendError, EntityError, EntityErrorFileNotFound


class MaterialEntityForTest(MaterialMixin):
    ENTITY_TYPE = "artifact"

    def __init__(self) -> None:
        self.project = "my-project"
        self.id = "entity-id"
        self.status = SimpleNamespace(files=None)
        self._context = Mock(return_value=SimpleNamespace(root=Path("/context")))
        self.update = Mock()
        self.refresh = Mock()


def _configure_material_upload(monkeypatch, store) -> None:
    monkeypatch.setattr(context_material, "get_store", Mock(return_value=store))

    def update_material_entity(entity):
        entity.update()
        return entity

    monkeypatch.setattr(
        material_mixin.material_processor,
        "_update_material_entity",
        update_material_entity,
    )


def test_init_material_extensions_defaults_to_empty_list() -> None:
    entity = MaterialEntityForTest()

    entity._init_material_extensions()

    assert entity.extensions == []


def test_as_file_downloads_to_store_temp_directory_and_cleans_up(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    download_dirs = []

    def download(_src, dst):
        download_dirs.append(dst)
        return [str(dst / "file.txt")]

    store.download.side_effect = download
    monkeypatch.setattr(material_mixin, "get_store", Mock(return_value=store))

    with entity.as_file() as result:
        assert result == [str(download_dirs[0] / "file.txt")]
        assert download_dirs[0].is_dir()

    assert not download_dirs[0].exists()
    store.download.assert_called_once_with("store://material", dst=download_dirs[0])


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
    _configure_material_upload(monkeypatch, store)

    entity.upload("/source", keep_dir_structure=True)

    assert entity.status.state == "READY"
    assert entity.status.message is None
    assert entity.status.files == [{"path": "file.txt"}]
    assert entity.update.call_count == 2
    entity.update.assert_any_call()
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
    _configure_material_upload(monkeypatch, store)
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
    _configure_material_upload(monkeypatch, store)

    with pytest.raises(EntityErrorFileNotFound, match="missing.txt"):
        entity.upload("/missing")

    assert entity.status.state == "ERROR"
    assert "Please verify" in entity.status.message
    assert entity.update.call_count == 2


def test_upload_converts_store_errors_to_entity_error(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store.upload.side_effect = ValueError("invalid source")
    _configure_material_upload(monkeypatch, store)

    with pytest.raises(EntityError, match="invalid source"):
        entity.upload("/source")

    assert entity.status.state == "ERROR"
    assert entity.status.message == "Upload failed: invalid source"
    assert entity.update.call_count == 2


def test_upload_converts_unexpected_errors_and_persists_error_state(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store.upload.side_effect = RuntimeError("unexpected storage failure")
    _configure_material_upload(monkeypatch, store)

    with pytest.raises(EntityError, match="unexpected storage failure") as error:
        entity.upload("/source")

    assert isinstance(error.value.__cause__, RuntimeError)
    assert entity.status.state == "ERROR"
    assert entity.status.message == "Upload failed: unexpected storage failure"
    assert entity.update.call_count == 2


def test_upload_surfaces_error_status_persistence_failure(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    store = Mock()
    store.upload.side_effect = RuntimeError("unexpected storage failure")
    _configure_material_upload(monkeypatch, store)

    def fail_error_status_update(upload_entity):
        upload_entity.update()
        if upload_entity.status.state == "ERROR":
            raise OSError("status update failed")
        return upload_entity

    monkeypatch.setattr(
        material_mixin.material_processor,
        "_update_material_entity",
        fail_error_status_update,
    )

    with pytest.raises(EntityError, match="failed to persist ERROR status: status update failed") as error:
        entity.upload("/source")

    assert isinstance(error.value.__cause__, OSError)
    assert entity.status.state == "ERROR"
    assert "unexpected storage failure" in entity.status.message
    assert entity.update.call_count == 2


def test_upload_delegates_to_material_processor(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    upload_material = Mock()
    monkeypatch.setattr(
        material_mixin.material_processor,
        "upload_material",
        upload_material,
    )

    entity.upload("/source", keep_dir_structure=True)

    upload_material.assert_called_once_with(
        entity,
        "/source",
        keep_dir_structure=True,
    )


def test_log_material_entity_uses_shared_upload_transaction(monkeypatch) -> None:
    processor = context_material.ContextEntityMaterialProcessor(Mock())
    entity = SimpleNamespace(
        spec=SimpleNamespace(path="store://material"),
        status=SimpleNamespace(state=None, message=None, files=None),
        _update_files_info=Mock(),
    )
    store = Mock()
    store.upload.return_value = ["file.txt"]
    store.get_file_info.return_value = [{"path": "file.txt"}]
    monkeypatch.setattr(context_material, "get_store", Mock(return_value=store))
    monkeypatch.setattr(processor, "_create_material_entity", Mock(return_value=entity))
    uploaded_states = []

    def update_material_entity(upload_entity):
        uploaded_states.append(upload_entity.status.state)
        return upload_entity

    monkeypatch.setattr(processor, "_update_material_entity", update_material_entity)

    result = processor.log_material_entity(
        source="/source",
        keep_dir_structure=True,
    )

    assert result is entity
    processor._create_material_entity.assert_called_once_with()
    assert uploaded_states == ["UPLOADING", "READY"]
    store.upload.assert_called_once_with(
        "/source",
        "store://material",
        keep_dir_structure=True,
    )
    entity._update_files_info.assert_called_once_with([{"path": "file.txt"}])


def test_update_material_entity_mutates_original_entity() -> None:
    crud_processor = Mock()
    processor = context_material.ContextEntityMaterialProcessor(crud_processor)
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = "artifact"
    entity.id = "entity-id"
    entity.to_dict.return_value = {"id": "entity-id"}
    updated_entity = Mock()
    crud_processor.update_context_entity.return_value = updated_entity

    result = processor._update_material_entity(entity)

    assert result is entity
    crud_processor.update_context_entity.assert_called_once_with(
        "my-project",
        "artifact",
        "entity-id",
        {"id": "entity-id"},
    )
    entity._update_attributes.assert_called_once_with(updated_entity)


def test_files_reads_backend_info_and_falls_back_to_status(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="store://material")
    entity.status.files = [{"path": "status.txt"}]
    read_files_info = Mock(return_value=[{"path": "backend.txt"}])
    monkeypatch.setattr(material_mixin.material_processor, "read_files_info", read_files_info)

    backend_files = entity.files
    assert backend_files[0].path == "backend.txt"
    assert backend_files[0].name is None
    assert entity.status.files == [{"path": "status.txt"}]
    read_files_info.assert_called_once_with(
        project="my-project",
        entity_type="artifact",
        entity_id="entity-id",
    )

    read_files_info.reset_mock()
    read_files_info.side_effect = BackendError("backend unavailable")

    status_files = entity.files
    assert status_files[0].path == "status.txt"
    assert entity.status.files == [{"path": "status.txt"}]


@pytest.mark.parametrize(
    ("material_path", "file_path", "expected_source"),
    [
        ("s3://bucket/material", "nested/file.txt", "s3://bucket/material"),
        (
            "s3://bucket/material/",
            "nested/file.txt",
            "s3://bucket/material/nested/file.txt",
        ),
        (
            "s3://bucket/artifact/untitled/id/Untitled.ipynb",
            "Untitled.ipynb",
            "s3://bucket/artifact/untitled/id/Untitled.ipynb",
        ),
    ],
)
@pytest.mark.parametrize(
    ("destination", "expected_destination"),
    [(None, Path("/context/artifact")), ("/tmp/download", Path("/tmp/download"))],
)
def test_material_file_download_uses_material_path_and_destination(
    material_path: str,
    file_path: str,
    expected_source: str,
    destination: str | None,
    expected_destination: Path,
    monkeypatch,
) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path=material_path)
    entity.status.files = [{"path": "status.txt"}]
    entity._context = Mock(return_value=SimpleNamespace(root=Path("/context")))
    monkeypatch.setattr(
        material_mixin.material_processor,
        "read_files_info",
        Mock(return_value=[{"path": file_path}]),
    )
    store = Mock()
    store.download.return_value = "/downloaded/file.txt"
    get_store = Mock(return_value=store)
    monkeypatch.setattr(material_files, "get_store", get_store)

    result = entity.files[0].download(destination=destination, overwrite=True)

    assert result == "/downloaded/file.txt"
    get_store.assert_called_once_with(material_path)
    store.download.assert_called_once_with(
        expected_source,
        expected_destination,
        overwrite=True,
    )


def test_material_file_as_file_downloads_and_cleans_up(monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.spec = SimpleNamespace(path="s3://bucket/material/")
    entity.status.files = [{"path": "status.txt"}]
    monkeypatch.setattr(
        material_mixin.material_processor,
        "read_files_info",
        Mock(return_value=[{"path": "nested/file.txt"}]),
    )
    store = Mock()
    download_dirs = []

    def download(_src, dst):
        download_dirs.append(dst)
        return str(dst / "file.txt")

    store.download.side_effect = download
    get_store = Mock(return_value=store)
    monkeypatch.setattr(material_files, "get_store", get_store)

    with entity.files[0].as_file() as result:
        assert result == str(download_dirs[0] / "file.txt")
        assert download_dirs[0].is_dir()

    assert not download_dirs[0].exists()
    get_store.assert_called_once_with("s3://bucket/material/")
    store.download.assert_called_once_with(
        "s3://bucket/material/nested/file.txt",
        dst=download_dirs[0],
    )


def test_material_file_repr_shows_non_none_metadata_as_dict() -> None:
    file = material_files.MaterialFile(
        path="trick.txt",
        name="trick.txt",
        content_type="text/plain",
        size=643,
        hash=None,
        last_modified=None,
        material_path="s3://bucket/material/",
        context_root=Path("/context/artifact"),
    )

    assert repr(file) == "{'path': 'trick.txt', 'name': 'trick.txt', 'content_type': 'text/plain', 'size': 643}"
