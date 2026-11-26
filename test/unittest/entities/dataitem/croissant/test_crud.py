import os
from unittest.mock import Mock

import pytest

import digitalhub.entities.dataitem.croissant.crud as crud_module
from digitalhub.utils.exceptions import EntityErrorFileNotFound


@pytest.mark.parametrize("error", [EntityErrorFileNotFound("missing"), RuntimeError("backend down")])
def test_log_croissant_restores_the_working_directory_when_logging_fails(monkeypatch, tmp_path, error) -> None:
    metadata = tmp_path / "croissant" / "metadata.json"
    metadata.parent.mkdir()
    monkeypatch.setattr(crud_module, "validate_croissant_source", Mock(return_value=str(metadata)))
    monkeypatch.setattr(crud_module, "build_croissant_kwargs", Mock(return_value={}))
    monkeypatch.setattr(crud_module, "get_croissant_dataset", Mock())
    monkeypatch.setattr(crud_module, "get_files_from_croissant", Mock(return_value=[]))
    monkeypatch.setattr(crud_module, "log_base_dataitem", Mock(side_effect=error))
    monkeypatch.chdir(tmp_path)

    with pytest.raises(type(error)):
        crud_module.log_croissant("project", "data", str(metadata))

    assert os.getcwd() == str(tmp_path)
