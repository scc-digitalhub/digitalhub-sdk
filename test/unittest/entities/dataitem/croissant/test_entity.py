from unittest.mock import Mock

from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant
from digitalhub.entities.dataitem.croissant.processor import DataitemCroissantProcessor


def test_as_dataset_delegates_to_the_croissant_processor(monkeypatch) -> None:
    entity = object.__new__(DataitemCroissant)
    entity.refresh = Mock()
    as_dataset = Mock(return_value="dataset")
    monkeypatch.setattr(DataitemCroissantProcessor, "as_dataset", as_dataset)

    assert entity.as_dataset(overwrite=True) == "dataset"

    entity.refresh.assert_called_once_with()
    as_dataset.assert_called_once_with(entity, overwrite=True)
