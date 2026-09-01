from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.material.mixin as material_mixin
from digitalhub.entities._mixin.material.mixin import MaterialMixin


class MaterialEntityForTest(MaterialMixin):
    ENTITY_TYPE = "artifact"

    def __init__(self) -> None:
        self.project = "my-project"
        self.id = "entity-id"
        self.status = SimpleNamespace(files=None)
        self.save = Mock()


@pytest.mark.parametrize("file_count", [0, 100])
def test_update_files_info_stores_small_file_sets_on_status(file_count: int, monkeypatch) -> None:
    entity = MaterialEntityForTest()
    files_info = [{"path": f"file-{index}"} for index in range(file_count)]
    update_files_info = Mock()
    monkeypatch.setattr(material_mixin.material_processor, "update_files_info", update_files_info)

    entity._update_files_info(files_info)

    assert entity.status.files == files_info
    update_files_info.assert_not_called()


@pytest.mark.parametrize("initial_files", [None, [{"path": "small-file"}]])
def test_update_files_info_uses_files_api_without_migrating_status_files(initial_files, monkeypatch) -> None:
    entity = MaterialEntityForTest()
    entity.status.files = initial_files
    files_info = [{"path": f"file-{index}"} for index in range(101)]
    update_files_info = Mock()
    monkeypatch.setattr(material_mixin.material_processor, "update_files_info", update_files_info)

    entity._update_files_info(files_info)

    assert entity.status.files == []
    entity.save.assert_called_once_with(update=True)
    update_files_info.assert_called_once_with(
        "my-project",
        "artifact",
        "entity-id",
        files_info,
    )
