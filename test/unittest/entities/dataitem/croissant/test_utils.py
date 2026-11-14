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
