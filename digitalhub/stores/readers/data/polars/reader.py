# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from io import BytesIO
from typing import IO, Any

import polars as pl
from polars.exceptions import ComputeError

from digitalhub.stores.readers.data._base.reader import DataframeReader
from digitalhub.stores.readers.data.polars.utils import (
    map_read_function,
    map_type,
    map_write_function,
    serialize_deserialize_preview,
)
from digitalhub.utils.data_utils import TableSchema, check_preview_size, finalize_preview, prepare_data, prepare_preview
from digitalhub.utils.exceptions import ReaderError


class DataframeReaderPolars(DataframeReader):
    """
    Polars reader class.
    """

    ROW_LIMIT_ARG = "n_rows"

    ##############################
    # Read methods
    ##############################

    def read_df(self, path_or_buffer: str | IO, extension: str, **kwargs) -> pl.DataFrame:
        """
        Read DataFrame from path or buffer.

        Parameters
        ----------
        path_or_buffer : str | IO
            Path or buffer to read DataFrame from.
        extension : str
            Extension of the file.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame.
        """
        read_function = map_read_function(extension)
        try:
            return read_function(path_or_buffer, **kwargs)
        except ComputeError as e:
            raise ReaderError(f"Error reading data with Polars: {str(e)}") from e
        except Exception as e:
            raise ReaderError(f"Unexpected error reading data with Polars: {str(e)}") from e

    def read_table(self, sql: str, engine: Any, **kwargs) -> pl.DataFrame:
        """
        Read table from db.

        Parameters
        ----------
        sql : str
            SQL query.
        engine : Any
            SQL Engine.
        **kwargs
            Keyword arguments.

        Returns
        -------
        pl.DataFrame
            Polars DataFrame.
        """
        return pl.read_database(query=sql, connection=engine, **kwargs)

    ##############################
    # Write methods
    ##############################

    def write_df(
        self,
        df: pl.DataFrame,
        dst: str | BytesIO,
        extension: str | None = None,
        **kwargs,
    ) -> None:
        """
        Write DataFrame.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        extension : str | None
            The extension of the file.
        **kwargs : dict
            Keyword arguments.
        """
        write_function = map_write_function(extension)
        try:
            write_function(df, dst, **kwargs)
        except ComputeError as e:
            raise ReaderError(f"Error writing data with Polars: {str(e)}") from e
        except Exception as e:
            raise ReaderError(f"Unexpected error writing data with Polars: {str(e)}") from e

    @staticmethod
    def write_table(df: pl.DataFrame, table: str, engine: Any, schema: str | None = None, **kwargs) -> None:
        """
        Write DataFrame as table.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe to write.
        table : str
            The destination table.
        engine : Any
            SQL Engine.
        schema : str
            The destination schema.
        **kwargs : dict
            Keyword arguments.
        """
        if "if_exists" in kwargs:
            kwargs["if_table_exists"] = kwargs.pop("if_exists")
        if "index" in kwargs:
            kwargs.pop("index")

        df.write_database(table_name=table, connection=engine, **kwargs)

    ##############################
    # Utils
    ##############################

    @staticmethod
    def concat_dfs(dfs: list[pl.DataFrame]) -> pl.DataFrame:
        """
        Concatenate a list of DataFrames.

        Parameters
        ----------
        dfs : list[pl.DataFrame]
            The DataFrames to concatenate.

        Returns
        -------
        pl.DataFrame
            The concatenated DataFrame.
        """
        return pl.concat(dfs)

    @staticmethod
    def get_schema(df: pl.DataFrame) -> dict:
        """
        Get schema.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe.

        Returns
        -------
        dict
            The schema.
        """
        schema = TableSchema()
        for column_name, dtype in df.schema.items():
            schema.add_field(str(column_name), map_type(dtype))
        return schema.to_dict()

    @staticmethod
    def get_preview(df: pl.DataFrame) -> dict:
        """
        Get preview.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe.

        Returns
        -------
        Any
            The preview.
        """
        columns = df.columns
        head = df.head(10)
        data = head.rows()
        prepared_data = prepare_data(data)
        preview = prepare_preview(columns, prepared_data)
        finalizes = finalize_preview(preview, df.height)
        serialized = serialize_deserialize_preview(finalizes)
        return check_preview_size(serialized)

    @staticmethod
    def get_limit_arg_name() -> str:
        """
        Get limit argument name for read methods.

        Returns
        -------
        str
            The limit argument name.
        """
        return "n_rows"
