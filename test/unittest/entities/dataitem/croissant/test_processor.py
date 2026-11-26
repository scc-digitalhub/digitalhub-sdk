from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import digitalhub.entities.dataitem.croissant.processor as processor_module
from digitalhub.entities.dataitem.croissant.processor import DataitemCroissantProcessor


def test_as_dataset_downloads_s3_files_and_maps_them(monkeypatch, tmp_path) -> None:
    obj = SimpleNamespace(spec=SimpleNamespace(path="s3://bucket/data/"), project="demo", ENTITY_TYPE="dataitem")
    store = Mock()
    store.download.side_effect = ["metadata.json", None]
    get_store = Mock(return_value=store)
    monkeypatch.setattr(processor_module, "get_store", get_store)
    monkeypatch.setattr(processor_module, "get_context", Mock(return_value=SimpleNamespace(root=tmp_path)))
    monkeypatch.setattr(processor_module, "get_files_from_croissant", Mock(return_value=[r"nested\group\file.csv"]))
    monkeypatch.setattr(processor_module, "get_mappings_from_croissant", Mock(return_value={"file": "/local/file.csv"}))
    get_dataset = Mock(side_effect=["dataset", "mapped-dataset"])
    monkeypatch.setattr(processor_module, "get_croissant_dataset", get_dataset)

    result = DataitemCroissantProcessor().as_dataset(obj, overwrite=True)

    assert result == "mapped-dataset"
    get_store.assert_called_once_with("s3://bucket/data/", "demo")
    root = tmp_path / "dataitem"
    assert store.download.call_args_list == [
        call("s3://bucket/data/metadata.json", root, overwrite=True),
        call("s3://bucket/data/nested/group/file.csv", root / Path("nested/group/file.csv"), overwrite=True),
    ]
    assert get_dataset.call_args_list == [
        call("metadata.json"),
        call("metadata.json", mapping={"file": "/local/file.csv"}),
    ]


def test_as_dataset_reads_remote_metadata_in_place(monkeypatch) -> None:
    obj = SimpleNamespace(spec=SimpleNamespace(path="https://example.com/metadata.json"), project="demo")
    get_store = Mock()
    monkeypatch.setattr(processor_module, "get_store", get_store)
    get_dataset = Mock(return_value="dataset")
    monkeypatch.setattr(processor_module, "get_croissant_dataset", get_dataset)

    assert DataitemCroissantProcessor().as_dataset(obj) == "dataset"

    get_dataset.assert_called_once_with("https://example.com/metadata.json")
    get_store.assert_not_called()


def test_as_dataset_downloads_local_metadata(monkeypatch, tmp_path) -> None:
    obj = SimpleNamespace(
        spec=SimpleNamespace(path="./croissant/metadata.json"), project="demo", ENTITY_TYPE="dataitem"
    )
    store = Mock()
    store.download.return_value = "downloaded/metadata.json"
    monkeypatch.setattr(processor_module, "get_store", Mock(return_value=store))
    monkeypatch.setattr(processor_module, "get_context", Mock(return_value=SimpleNamespace(root=tmp_path)))
    get_dataset = Mock(return_value="dataset")
    monkeypatch.setattr(processor_module, "get_croissant_dataset", get_dataset)

    assert DataitemCroissantProcessor().as_dataset(obj) == "dataset"

    store.download.assert_called_once_with("./croissant/metadata.json", tmp_path / "dataitem", overwrite=True)
    get_dataset.assert_called_once_with("downloaded/metadata.json")
