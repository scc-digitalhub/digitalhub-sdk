from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import digitalhub.entities.dataitem.croissant.entity as entity_module
from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant


def test_collect_local_data_normalizes_s3_key_separators(monkeypatch, tmp_path) -> None:
    entity = object.__new__(DataitemCroissant)
    entity.spec = SimpleNamespace(path="s3://bucket/data/")
    entity.project = "demo"
    entity._context = Mock(return_value=SimpleNamespace(root=tmp_path))
    store = Mock()
    get_store = Mock(return_value=store)
    monkeypatch.setattr(entity_module, "get_files_from_croissant", Mock(return_value=[r"nested\group\file.csv"]))
    monkeypatch.setattr(entity_module, "get_store", get_store)

    entity._collect_local_data(Mock(), "metadata.json", overwrite=True)

    get_store.assert_called_once_with("s3://bucket/data/", "demo")

    store.download.assert_called_once_with(
        "s3://bucket/data/nested/group/file.csv",
        tmp_path / entity.ENTITY_TYPE / Path("nested/group/file.csv"),
        overwrite=True,
    )


def test_as_dataset_reuses_downloaded_metadata_path(monkeypatch) -> None:
    entity = object.__new__(DataitemCroissant)
    entity.spec = SimpleNamespace(path="https://example.com/metadata.json")
    entity.refresh = Mock()
    entity._get_metadata_json = Mock(return_value="metadata.json")
    entity._collect_local_data = Mock()
    entity._map_files_filepaths = Mock(return_value={"file.csv": "/local/file.csv"})
    get_dataset = Mock(side_effect=["dataset", "mapped-dataset"])
    monkeypatch.setattr(entity_module, "get_croissant_dataset", get_dataset)

    assert entity.as_dataset() == "mapped-dataset"

    entity._get_metadata_json.assert_called_once_with()
    entity._collect_local_data.assert_called_once_with("dataset", "metadata.json", overwrite=False)
    entity._map_files_filepaths.assert_called_once_with("dataset", "metadata.json")
    get_dataset.assert_has_calls(
        [
            call("metadata.json"),
            call("metadata.json", mapping={"file.csv": "/local/file.csv"}),
        ]
    )
