# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from io import BytesIO
from typing import IO, Any

import polars as pl
from polars.exceptions import ComputeError

from digitalhub.stores.readers.data._base.reader import DataframeReader
from digitalhub.utils.data_utils import check_preview_size, finalize_preview, prepare_data, prepare_preview
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.exceptions import ReaderError
from digitalhub.utils.generic_utils import CustomJsonEncoder


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
        if extension == FileExtensions.CSV.value:
            return pl.read_csv(path_or_buffer, **kwargs)
        if extension == FileExtensions.PARQUET.value:
            return pl.read_parquet(path_or_buffer, **kwargs)
        if extension == FileExtensions.JSON.value:
            return pl.read_json(path_or_buffer, **kwargs)
        if extension in (FileExtensions.EXCEL.value, FileExtensions.EXCEL_OLD.value):
            return pl.read_excel(path_or_buffer, **kwargs)
        if extension in (FileExtensions.TXT.value, FileExtensions.FILE.value):
            try:
                return self.read_df(path_or_buffer, FileExtensions.CSV.value, **kwargs)
            except ComputeError:
                raise ReaderError(f"Unable to read from {path_or_buffer}.")
        else:
            raise ReaderError(f"Unsupported extension '{extension}' for reading.")

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
        if extension == FileExtensions.CSV.value:
            return self.write_csv(df, dst, **kwargs)
        if extension == FileExtensions.PARQUET.value:
            return self.write_parquet(df, dst, **kwargs)
        raise ReaderError(f"Unsupported extension '{extension}' for writing.")

    @staticmethod
    def write_csv(df: pl.DataFrame, dst: str | BytesIO, **kwargs) -> None:
        """
        Write DataFrame as csv.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.
        """
        df.write_csv(dst, **kwargs)

    @staticmethod
    def write_parquet(df: pl.DataFrame, dst: str | BytesIO, **kwargs) -> None:
        """
        Write DataFrame as parquet.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.
        """
        df.write_parquet(dst, **kwargs)

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
    def get_schema(df: pl.DataFrame) -> Any:
        """
        Get schema.

        Parameters
        ----------
        df : pl.DataFrame
            The dataframe.

        Returns
        -------
        Any
            The schema.
        """
        schema = {"fields": []}

        for column_name, dtype in df.schema.items():
            field = {"name": str(column_name), "type": ""}

            if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64):
                field["type"] = "integer"
            elif dtype in (pl.Float32, pl.Float64, pl.Decimal):
                field["type"] = "number"
            elif dtype == pl.Boolean:
                field["type"] = "boolean"
            elif dtype in (pl.Utf8, pl.String, pl.Categorical):
                field["type"] = "string"
            elif dtype in (pl.Date, pl.Datetime, pl.Time, pl.Duration):
                field["type"] = "datetime"
            else:
                field["type"] = "any"

            schema["fields"].append(field)

        return schema

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
        serialized = _serialize_deserialize_preview(finalizes)
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


class PolarsJsonEncoder(CustomJsonEncoder):
    """
    JSON serializer.
    """

    def default(self, obj: Any) -> Any:
        """
        Serializer.

        Parameters
        ----------
        obj : Any
            The object to serialize.

        Returns
        -------
        Any
            The serialized object.
        """
        return super().default(obj)


def _serialize_deserialize_preview(preview: dict) -> dict:
    """
    Serialize and deserialize preview.

    Parameters
    ----------
    preview : dict
        The preview.

    Returns
    -------
    dict
        The serialized preview.
    """
    return json.loads(json.dumps(preview, cls=PolarsJsonEncoder))
