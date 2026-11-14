# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, Mock

import pytest

from digitalhub.stores.data._base import store as base_store_module
from digitalhub.stores.data.sql import store as store_module
from digitalhub.stores.data.sql.store import SqlStore
from digitalhub.utils.exceptions import StoreError


def test_check_access_to_storage_closes_probe_connection() -> None:
    engine = Mock()
    connection = MagicMock()
    engine.connect.return_value = connection

    SqlStore._check_access_to_storage(engine)

    connection.__exit__.assert_called_once()


def test_build_temp_accepts_optional_prefix(monkeypatch, tmp_path) -> None:
    mkdtemp = Mock(return_value=str(tmp_path))
    monkeypatch.setattr(base_store_module, "mkdtemp", mkdtemp)

    assert base_store_module.Store._build_temp() == tmp_path
    mkdtemp.assert_called_once_with(prefix=None)

    mkdtemp.reset_mock()
    assert base_store_module.Store._build_temp("sql_") == tmp_path
    mkdtemp.assert_called_once_with(prefix="sql_")


def test_download_without_destination_uses_prefixed_temp_directory(monkeypatch, tmp_path) -> None:
    mkdtemp = Mock(return_value=str(tmp_path))
    monkeypatch.setattr(base_store_module, "mkdtemp", mkdtemp)
    store = object.__new__(SqlStore)
    store._download_table = Mock(return_value="downloaded")

    assert store.download("sql://database/schema/items", None) == "downloaded"

    mkdtemp.assert_called_once_with(prefix="sql_")
    store._download_table.assert_called_once_with(
        "schema",
        "items",
        str(tmp_path / "items.parquet"),
        database="database",
    )


@pytest.mark.parametrize("scheme", ["sql", "postgresql"])
def test_parse_path_accepts_registered_sql_schemes(scheme: str) -> None:
    assert SqlStore._parse_path(f"{scheme}://database/schema/items") == {
        "database": "database",
        "schema": "schema",
        "table": "items",
    }


def test_check_factory_rejects_uri_database_mismatch() -> None:
    store = object.__new__(SqlStore)
    store._configurator = Mock()
    store._configurator.get_sql_conn_string.return_value = "connection-string"
    engine = Mock()
    engine.url.database = "configured"
    store._get_engine = Mock(return_value=engine)
    store._check_access_to_storage = Mock()

    with pytest.raises(StoreError, match="requested.*configured"):
        store._check_factory(database="requested")

    engine.dispose.assert_called_once_with()
    store._check_access_to_storage.assert_not_called()


def test_check_factory_accepts_matching_uri_database() -> None:
    store = object.__new__(SqlStore)
    store._configurator = Mock()
    store._configurator.get_sql_conn_string.return_value = "connection-string"
    engine = Mock()
    engine.url.database = "configured"
    store._get_engine = Mock(return_value=engine)
    store._check_access_to_storage = Mock()

    assert store._check_factory(database="configured") is engine

    store._check_access_to_storage.assert_called_once_with(engine)


def test_write_df_passes_uri_database_to_upload_table() -> None:
    store = object.__new__(SqlStore)
    dataframe = object()
    store._upload_table = Mock(return_value="written")

    assert store.write_df(dataframe, "postgresql://database/schema/items") == "written"

    store._upload_table.assert_called_once_with(dataframe, "schema", "items", database="database")


def test_upload_table_passes_schema_to_factory(monkeypatch) -> None:
    store = object.__new__(SqlStore)
    dataframe = object()
    reader = Mock()
    engine = Mock()
    engine.url.database = "database"
    monkeypatch.setattr(store_module, "get_reader_by_object", Mock(return_value=reader))
    store._check_factory = Mock(return_value=engine)

    assert store._upload_table(dataframe, "analytics", "items", database="database") == (
        "sql://database/analytics/items"
    )

    store._check_factory.assert_called_once_with(schema="analytics", database="database")
    reader.write_table.assert_called_once_with(dataframe, "items", engine, "analytics")
    engine.dispose.assert_called_once_with()


def test_create_vector_table_passes_uri_database_to_factory() -> None:
    store = object.__new__(SqlStore)
    engine = MagicMock()
    store._check_factory = Mock(return_value=engine)

    assert store.create_vector_table("postgresql://database/schema/items", "CREATE TABLE items") == ("schema", "items")

    store._check_factory.assert_called_once_with(schema="schema", database="database")
    engine.dispose.assert_called_once_with()


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

    store._check_factory.assert_called_once_with(schema="public", database="database")
    engine.dispose.assert_called_once_with()
