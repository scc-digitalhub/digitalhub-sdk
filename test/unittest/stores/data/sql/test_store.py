# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from threading import RLock
from unittest.mock import MagicMock, Mock, call

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from sqlalchemy import create_engine, text

from digitalhub.stores.data._base import store as base_store_module
from digitalhub.stores.data.sql import store as store_module
from digitalhub.stores.data.sql.store import MAX_SQL_CONNECTION_RETRIES, SqlStore
from digitalhub.utils.exceptions import ConfigError, StoreError


def test_get_engine_reuses_connections_by_url_and_schema(monkeypatch) -> None:
    store = object.__new__(SqlStore)
    store._engines = {}
    store._engine_lock = RLock()
    first_engine = Mock()
    second_engine = Mock()
    third_engine = Mock()
    create_engine = Mock(side_effect=[first_engine, second_engine, third_engine])
    monkeypatch.setattr(store_module, "create_engine", create_engine)

    assert store._get_engine("connection-one", "schema-one") is first_engine
    assert store._get_engine("connection-one", "schema-one") is first_engine
    assert store._get_engine("connection-one", "schema-two") is second_engine
    assert store._get_engine("connection-two", "schema-one") is third_engine

    assert create_engine.call_args_list == [
        call(
            "connection-one",
            connect_args={
                "timeout": store_module.ENGINE_CONNECTION_TIMEOUT,
                "startup_params": {"search_path": "schema-one"},
            },
            pool_pre_ping=True,
        ),
        call(
            "connection-one",
            connect_args={
                "timeout": store_module.ENGINE_CONNECTION_TIMEOUT,
                "startup_params": {"search_path": "schema-two"},
            },
            pool_pre_ping=True,
        ),
        call(
            "connection-two",
            connect_args={
                "timeout": store_module.ENGINE_CONNECTION_TIMEOUT,
                "startup_params": {"search_path": "schema-one"},
            },
            pool_pre_ping=True,
        ),
    ]


def test_close_disposes_and_clears_cached_engines() -> None:
    store = object.__new__(SqlStore)
    store._engines = {("connection", None): Mock(), ("connection", "schema"): Mock()}
    store._engine_lock = RLock()
    engines = list(store._engines.values())

    store.close()

    assert store._engines == {}
    for engine in engines:
        engine.dispose.assert_called_once_with()


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

    with pytest.raises(StoreError, match="requested.*configured"):
        store._check_factory(database="requested")

    engine.dispose.assert_not_called()
    engine.connect.assert_not_called()


def test_check_factory_accepts_matching_uri_database() -> None:
    store = object.__new__(SqlStore)
    store._configurator = Mock()
    store._configurator.get_sql_conn_string.return_value = "connection-string"
    engine = Mock()
    engine.url.database = "configured"
    store._get_engine = Mock(return_value=engine)

    assert store._check_factory(database="configured") is engine

    engine.connect.assert_not_called()


def test_check_factory_retries_configuration_errors_with_a_bounded_loop() -> None:
    store = object.__new__(SqlStore)
    store._configurator = Mock()
    store._configurator.get_sql_conn_string.side_effect = ConfigError("credentials unavailable")
    store._configurator.eval_retry.return_value = True
    store._get_engine = Mock()

    with pytest.raises(ConfigError, match="credentials unavailable"):
        store._check_factory()

    assert store._configurator.get_sql_conn_string.call_count == MAX_SQL_CONNECTION_RETRIES
    assert store._configurator.eval_retry.call_count == MAX_SQL_CONNECTION_RETRIES - 1
    store._get_engine.assert_not_called()


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
    engine.dispose.assert_not_called()


def test_create_vector_table_passes_uri_database_to_factory() -> None:
    store = object.__new__(SqlStore)
    engine = MagicMock()
    store._check_factory = Mock(return_value=engine)

    assert store.create_vector_table("postgresql://database/schema/items", "CREATE TABLE items") == ("schema", "items")

    store._check_factory.assert_called_once_with(schema="schema", database="database")
    engine.dispose.assert_not_called()


def test_read_df_keeps_cached_engine_when_reader_fails(monkeypatch) -> None:
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
    engine.dispose.assert_not_called()


def test_download_table_streams_batches_and_handles_null_first_batch(tmp_path) -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE items (id INTEGER NOT NULL, label TEXT)")
        connection.execute(
            text("INSERT INTO items (id, label) VALUES (:id, :label)"),
            [{"id": index, "label": None if index < 10_000 else "last"} for index in range(10_001)],
        )

    store = object.__new__(SqlStore)
    store._check_factory = Mock(return_value=engine)
    destination = str(tmp_path / "items.parquet")

    assert store._download_table("main", "items", destination) == destination

    table = pq.read_table(destination)
    assert table.num_rows == 10_001
    assert table.column("label").type == pa.string()
    assert table.column("label").to_pylist()[-1] == "last"


def test_download_table_writes_empty_parquet_table(tmp_path) -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE items (id INTEGER NOT NULL)")

    store = object.__new__(SqlStore)
    store._check_factory = Mock(return_value=engine)
    destination = str(tmp_path / "items.parquet")

    assert store._download_table("main", "items", destination) == destination
    assert pq.read_table(destination).num_rows == 0
