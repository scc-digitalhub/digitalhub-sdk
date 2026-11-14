from inspect import signature
from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.dataitem.table.entity as table_entity_module
from digitalhub.entities.dataitem.table.crud import log_table
from digitalhub.entities.dataitem.table.entity import DataitemTable


def test_table_reader_apis_use_factory_default_engine() -> None:
    assert signature(log_table).parameters["engine"].default is None


def test_as_df_uses_factory_default_engine_when_omitted(monkeypatch) -> None:
    entity = object.__new__(DataitemTable)
    entity.spec = SimpleNamespace(path="s3://bucket/table.csv")
    entity.refresh = Mock()
    store = Mock()
    monkeypatch.setattr(table_entity_module, "get_store", Mock(return_value=store))

    entity.as_df()

    store.read_df.assert_called_once_with("s3://bucket/table.csv", None, None)
