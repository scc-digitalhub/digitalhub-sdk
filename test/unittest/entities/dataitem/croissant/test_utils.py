import os
from unittest.mock import Mock

import pytest

import digitalhub.entities.dataitem.croissant.utils as croissant_utils


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires POSIX FIFO support")
def test_validate_croissant_source_rejects_special_file(tmp_path) -> None:
    fifo = tmp_path / "source.json"
    os.mkfifo(fifo)

    with pytest.raises(ValueError, match="not a regular file or directory"):
        croissant_utils.validate_croissant_source(str(fifo))


def test_validate_croissant_source_accepts_metadata_file(monkeypatch, tmp_path) -> None:
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text("{}")
    monkeypatch.setattr(croissant_utils, "get_croissant_dataset", Mock())

    assert croissant_utils.validate_croissant_source(str(metadata_file)) == str(metadata_file.resolve())


def test_build_croissant_kwargs_uses_explicit_default_store(monkeypatch) -> None:
    monkeypatch.setattr(croissant_utils, "build_uuid", Mock(return_value="entity-id"))
    build_path = Mock(return_value="s3://bucket/project/dataitem/catalog/entity-id/")
    monkeypatch.setattr(croissant_utils, "build_log_path_as_partition", build_path)

    result = croissant_utils.build_croissant_kwargs(
        "project",
        "dataitem",
        "catalog",
        default_store="s3://bucket",
    )

    assert result == {
        "uuid": "entity-id",
        "path": "s3://bucket/project/dataitem/catalog/entity-id/",
        "keep_dir_structure": True,
    }
    build_path.assert_called_once_with(
        "project",
        "dataitem",
        "catalog",
        "entity-id",
        default_store="s3://bucket",
    )
