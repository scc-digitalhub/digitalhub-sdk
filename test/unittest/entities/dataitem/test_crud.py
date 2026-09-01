from unittest.mock import Mock

import pytest

import digitalhub.entities.dataitem._base.crud as base_crud
import digitalhub.entities.dataitem.croissant.crud as croissant_crud
import digitalhub.entities.dataitem.dataitem.crud as dataitem_crud
import digitalhub.entities.dataitem.generic.crud as generic_crud
import digitalhub.entities.dataitem.table.crud as table_crud
from digitalhub.entities._commons.enums import EntityKinds


def test_register_dataitem_delegates_to_base_with_specific_kind(monkeypatch) -> None:
    register_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(dataitem_crud, "register_base_dataitem", register_base_dataitem)

    result = dataitem_crud.register_dataitem(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        name="data",
    )

    assert result == "dataitem"
    register_base_dataitem.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        entity_kind=EntityKinds.DATAITEM_DATAITEM.value,
        name="data",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_register_generic_dataitem_passes_dynamic_kind(monkeypatch) -> None:
    register_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(generic_crud, "register_base_dataitem", register_base_dataitem)

    result = generic_crud.register_generic_dataitem(
        project="my-project",
        kind="custom-dataitem",
        source="s3://my-bucket/data/data.csv",
    )

    assert result == "dataitem"
    register_base_dataitem.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        entity_kind="custom-dataitem",
        name=None,
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_register_base_dataitem_passes_source_as_path(monkeypatch) -> None:
    new_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(base_crud, "new_dataitem", new_dataitem)

    result = base_crud.register_base_dataitem(
        project="my-project",
        source=["s3://my-bucket/data/data.csv"],
        entity_kind=EntityKinds.DATAITEM_DATAITEM.value,
        name="data",
    )

    assert result == "dataitem"
    new_dataitem.assert_called_once_with(
        project="my-project",
        name="data",
        kind=EntityKinds.DATAITEM_DATAITEM.value,
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        path="s3://my-bucket/data/data.csv",
        extensions=None,
    )


@pytest.mark.parametrize(
    ("crud_module", "register_name", "entity_kind"),
    [
        (table_crud, "register_table", EntityKinds.DATAITEM_TABLE.value),
        (croissant_crud, "register_croissant", EntityKinds.DATAITEM_CROISSANT.value),
    ],
)
def test_register_dataitem_specialized_delegates_to_base(crud_module, register_name, entity_kind, monkeypatch) -> None:
    register_base_dataitem = Mock(return_value="dataitem")
    monkeypatch.setattr(crud_module, "register_base_dataitem", register_base_dataitem)

    result = getattr(crud_module, register_name)(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        name="data",
    )

    assert result == "dataitem"
    register_base_dataitem.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/data/data.csv",
        entity_kind=entity_kind,
        name="data",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )
