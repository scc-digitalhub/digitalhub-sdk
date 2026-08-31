from unittest.mock import MagicMock, Mock

import pytest

from digitalhub.stores.data.sql import store as store_module
from digitalhub.stores.data.sql.store import SqlStore


def test_check_access_to_storage_closes_probe_connection() -> None:
    engine = Mock()
    connection = MagicMock()
    engine.connect.return_value = connection

    SqlStore._check_access_to_storage(engine)

    connection.__exit__.assert_called_once()


def test_read_df_disposes_engine_when_reader_fails(monkeypatch) -> None:
    store = object.__new__(SqlStore)
    engine = Mock()
    reader = Mock()
    reader.read_table.side_effect = RuntimeError("read failed")
    store._get_reader = Mock(return_value=reader)
    store._get_schema = Mock(return_value="public")
    store._get_table_name = Mock(return_value="items")
    store._check_factory = Mock(return_value=engine)
    monkeypatch.setattr(store_module, "Table", Mock(return_value=Mock()))
    monkeypatch.setattr(store_module, "select", Mock(return_value=Mock()))

    with pytest.raises(RuntimeError, match="read failed"):
        store.read_df("sql://database/items")

    engine.dispose.assert_called_once_with()


def test_query_disposes_engine_when_reader_fails() -> None:
    store = object.__new__(SqlStore)
    engine = Mock()
    reader = Mock()
    reader.read_table.side_effect = RuntimeError("query failed")
    store._get_reader = Mock(return_value=reader)
    store._get_schema = Mock(return_value="public")
    store._check_factory = Mock(return_value=engine)

    with pytest.raises(RuntimeError, match="query failed"):
        store.query("SELECT 1", "sql://database/items")

    engine.dispose.assert_called_once_with()
