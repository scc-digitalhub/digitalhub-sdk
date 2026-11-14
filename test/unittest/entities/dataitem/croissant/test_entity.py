from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.dataitem.croissant.entity as entity_module
from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant


def test_collect_local_data_normalizes_s3_key_separators(monkeypatch, tmp_path) -> None:
    entity = object.__new__(DataitemCroissant)
    entity.spec = SimpleNamespace(path="s3://bucket/data/")
    entity._context = Mock(return_value=SimpleNamespace(root=tmp_path))
    store = Mock()
    monkeypatch.setattr(entity_module, "get_files_from_croissant", Mock(return_value=[r"nested\group\file.csv"]))
    monkeypatch.setattr(entity_module, "get_store", Mock(return_value=store))

    entity._collect_local_data(Mock(), "metadata.json", overwrite=True)

    store.download.assert_called_once_with(
        "s3://bucket/data/nested/group/file.csv",
        tmp_path / entity.ENTITY_TYPE / Path("nested/group/file.csv"),
        overwrite=True,
    )
