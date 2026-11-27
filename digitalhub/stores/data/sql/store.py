# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.engine import Engine

from digitalhub.stores.data._base.credentials import StoreCredentials
from digitalhub.stores.data._base.store import Store
from digitalhub.stores.data.sql.configurator import SqlStoreConfigurator
from digitalhub.stores.data.sql.utils import get_schema_from_columns
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.exceptions import ConfigError, StoreError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import Dataframe, SourcesOrListOfSources
from digitalhub.utils.uri_utils import parse_sql_path

logger = get_logger(__name__)

ENGINE_CONNECTION_TIMEOUT = 30
MAX_SQL_CONNECTION_RETRIES = 3
_BATCH_SIZE = 10_000


def _arrow_type_from_sqlalchemy(column_type: Any) -> pa.DataType | None:
    """Map common SQL scalar types to stable Arrow types across batches."""
    try:
        python_type = column_type.python_type
    except (AttributeError, NotImplementedError):
        return None

    if python_type is bool:
        return pa.bool_()
    if issubclass(python_type, int):
        return pa.int64()
    if issubclass(python_type, float):
        return pa.float64()
    if issubclass(python_type, str):
        return pa.string()
    if issubclass(python_type, bytes):
        return pa.binary()
    if issubclass(python_type, datetime):
        timezone = "UTC" if getattr(column_type, "timezone", False) else None
        return pa.timestamp("us", tz=timezone)
    if issubclass(python_type, date):
        return pa.date32()
    if issubclass(python_type, time):
        return pa.time64("us")
    if issubclass(python_type, Decimal):
        precision = getattr(column_type, "precision", None)
        scale = getattr(column_type, "scale", None) or 0
        if precision is not None:
            if precision <= 38:
                return pa.decimal128(precision, scale)
            return pa.decimal256(precision, scale)
    return None


class SqlStore(Store):
    """
    SQL-based data store implementation for database operations.

    Provides functionality for reading, writing, and managing data in SQL
    databases. Implements the Store interface and provides methods to fetch and persist
    artifacts on SQL based storage.

    Attributes
    ----------
    _configurator : SqlStoreConfigurator
        The configurator instance for managing SQL database credentials
        and connection parameters.
    """

    def __init__(self, credentials: StoreCredentials) -> None:
        super().__init__()
        self._configurator: SqlStoreConfigurator = SqlStoreConfigurator(credentials)
        self._engines: dict[tuple[str, str | None], Engine] = {}
        self._engine_lock = RLock()

    ##############################
    # I/O methods
    ##############################

    def download(
        self,
        src: str,
        dst: Path | None,
        overwrite: bool = False,
    ) -> str:
        """
        Download a SQL table as a Parquet file to local storage.
        """
        parsed = parse_sql_path(src)
        table_name = parsed["table"] + ".parquet"
        # Case where dst is not provided
        if dst is None:
            dst = Path(self._build_temp("sql_")) / table_name
        else:
            self._check_local_dst(str(dst))
            path = Path(dst)

            # Case where dst is a directory
            if path.suffix == "":
                dst = path / table_name

            # Case where dst is a file
            elif path.suffix != ".parquet":
                raise StoreError("The destination path must be a directory or a parquet file.")

            self._check_overwrite(dst, overwrite)
            self._build_path(dst)

        return self._download_table(parsed["schema"], parsed["table"], str(dst), database=parsed["database"])

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Get file metadata information from SQL storage.
        """
        return []

    ##############################
    # Datastore methods
    ##############################

    def read_df(
        self,
        path: SourcesOrListOfSources,
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Dataframe:  # type: ignore
        """
        Read a DataFrame from a SQL table.
        """
        if isinstance(path, list):
            raise StoreError("SQL store can only read a single DataFrame at a time.")

        reader = self._get_reader(engine)
        parsed = parse_sql_path(path)
        schema = parsed["schema"]
        table = parsed["table"]
        sql_engine = self._check_factory(schema=schema, database=parsed["database"])

        sa_table = Table(table, MetaData(), autoload_with=sql_engine)
        stm = select(sa_table)
        return reader.read_table(stm, sql_engine, **kwargs)

    def write_df(
        self,
        df: Any,
        dst: str,
        extension: str | None = None,
        **kwargs,
    ) -> str:
        """
        Write a DataFrame to a SQL database table.
        """
        parsed = parse_sql_path(dst)
        return self._upload_table(
            df,
            parsed["schema"],
            parsed["table"],
            database=parsed["database"],
            **kwargs,
        )

    ##############################
    # Utils methods
    ##############################

    def create_vector_table(self, path: str, sql: str) -> tuple[str, str]:
        """
        Create a SQL table with vector extension.
        """
        parsed = parse_sql_path(path)
        schema = parsed["schema"]
        table = parsed["table"]
        engine = self._check_factory(schema=schema, database=parsed["database"])
        with engine.begin() as connection:
            connection.exec_driver_sql(sql)
        return schema, table

    def get_schema_from_table(self, table: str, schema: str | None = None) -> dict:
        """
        Get the schema of a SQL table.
        """
        engine = self._check_factory(schema=schema)
        inspector = inspect(engine)
        columns = inspector.get_columns(table, schema=schema)
        return get_schema_from_columns(columns)

    ##############################
    # Wrapper methods
    ##############################

    def get_engine(self, schema: str | None = None) -> Engine:
        """
        Get or create a cached SQLAlchemy engine for the database configuration.
        """
        return self._check_factory(schema=schema)

    def get_credentials(self, lowercase_keys: bool = True) -> dict:
        """
        Get database credentials as a dictionary.
        """
        return self._configurator.get_credentials(lowercase_keys=lowercase_keys)

    ##############################
    # Private I/O methods
    ##############################

    def _download_table(self, schema: str, table: str, dst: str, database: str | None = None) -> str:
        """
        Download a specific table from SQL database to Parquet file.
        """
        engine = self._check_factory(schema=schema, database=database)

        # Read the table from the database in bounded batches.
        sa_table = Table(table, MetaData(), autoload_with=engine)
        stm = select(sa_table)
        columns = list(sa_table.columns)
        column_names = [column.name for column in columns]

        def to_arrow_table(rows: Sequence[Any]) -> pa.Table:
            arrays = []
            for index, column in enumerate(columns):
                values = [row[index] for row in rows]
                arrow_type = _arrow_type_from_sqlalchemy(column.type)
                arrays.append(pa.array(values, type=arrow_type) if arrow_type is not None else pa.array(values))
            return pa.Table.from_arrays(arrays, names=column_names)

        with engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(stm)
            partitions = iter(result.partitions(_BATCH_SIZE))
            first_partition = next(partitions, None)
            if first_partition is None:
                pq.write_table(pa.Table.from_pydict({name: [] for name in column_names}), dst)
                return dst

            first_table = to_arrow_table(first_partition)
            schema = first_table.schema
            with pq.ParquetWriter(dst, schema) as writer:
                writer.write_table(first_table)
                for rows in partitions:
                    arrow_table = to_arrow_table(rows)
                    if arrow_table.schema != schema:
                        arrow_table = arrow_table.cast(schema, safe=False)
                    writer.write_table(arrow_table)
        return dst

    def _upload_table(self, df: Any, schema: str, table: str, database: str | None = None, **kwargs) -> str:
        """
        Upload a DataFrame to a SQL table.
        """
        reader = get_reader_by_object(df)
        engine = self._check_factory(schema=schema, database=database)
        reader.write_table(df, table, engine, schema, **kwargs)
        return f"sql://{engine.url.database}/{schema}/{table}"

    ##############################
    # Helper methods
    ##############################

    def _get_engine(self, connection_string: str, schema: str | None = None) -> Engine:
        """
        Get or create a cached SQLAlchemy engine from the connection string.
        """
        connect_args = {"timeout": ENGINE_CONNECTION_TIMEOUT}
        if schema is not None:
            connect_args["startup_params"] = {"search_path": schema}
        key = (connection_string, schema)
        with self._engine_lock:
            engine = self._engines.get(key)
            if engine is None:
                engine = create_engine(
                    connection_string,
                    connect_args=connect_args,
                    pool_pre_ping=True,
                )
                self._engines[key] = engine
            return engine

    def close(self) -> None:
        """Dispose all cached SQL engines and clear the engine cache."""
        with self._engine_lock:
            engines = list(self._engines.values())
            self._engines.clear()
        for engine in engines:
            engine.dispose()

    def _check_factory(self, schema: str | None = None, database: str | None = None) -> Engine:
        """
        Return a cached engine and validate the database requested by the SQL URI.
        """
        for attempt in range(MAX_SQL_CONNECTION_RETRIES):
            try:
                connection_string = self._configurator.get_sql_conn_string()
                engine = self._get_engine(connection_string, schema)
                if database is not None and engine.url.database != database:
                    configured_database = engine.url.database
                    raise StoreError(
                        f"SQL URI database '{database}' does not match configured database '{configured_database}'."
                    )
                return engine
            except ConfigError:
                if attempt + 1 == MAX_SQL_CONNECTION_RETRIES or not self._configurator.eval_retry():
                    raise
                logger.debug("SQL connection setup failed, retrying with refreshed credentials.")

    def _get_table_name(self, uri: str) -> str:
        """
        Extract the table name from a SQL URI.
        """
        return str(parse_sql_path(uri).get("table"))
