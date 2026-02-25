# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from io import BytesIO
from typing import IO, Any

import numpy as np
import pandas as pd
from pandas.errors import ParserError

from digitalhub.stores.readers.data._base.reader import DataframeReader
from digitalhub.stores.readers.data.pandas.utils import (
    map_read_function,
    map_type,
    map_write_function,
    serialize_deserialize_preview,
)
from digitalhub.utils.data_utils import (
    TableSchema,
    check_preview_size,
    finalize_preview,
    prepare_data,
    prepare_preview,
)
from digitalhub.utils.exceptions import ReaderError


class DataframeReaderPandas(DataframeReader):
    """
    Pandas reader class.
    """

    ##############################
    # Read methods
    ##############################

    def read_df(self, path_or_buffer: str | IO, extension: str, **kwargs) -> pd.DataFrame:
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
        pd.DataFrame
            Pandas DataFrame.
        """
        read_function = map_read_function(extension)
        try:
            return read_function(path_or_buffer, **kwargs)
        except ParserError as e:
            raise ReaderError(f"Unable to read from {path_or_buffer}.") from e
        except ValueError as e:
            raise ReaderError(f"Unsupported extension '{extension}' for reading.") from e

    def read_table(self, sql: str, engine: Any, **kwargs) -> pd.DataFrame:
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
        pd.DataFrame
            Pandas DataFrame.
        """
        return pd.read_sql(sql=sql, con=engine, **kwargs)

    ##############################
    # Write methods
    ##############################

    def write_df(
        self,
        df: pd.DataFrame,
        dst: str | BytesIO,
        extension: str | None = None,
        **kwargs,
    ) -> None:
        """
        Write DataFrame as parquet.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to write.
        dst : str | BytesIO
            The destination of the dataframe.
        **kwargs : dict
            Keyword arguments.
        """
        if "index" not in kwargs:
            kwargs["index"] = False
        try:
            write_function = map_write_function(extension)
        except ValueError as e:
            raise ReaderError(f"Unsupported extension '{extension}' for writing.") from e
        return write_function(df, dst, **kwargs)

    @staticmethod
    def write_table(df: pd.DataFrame, table: str, engine: Any, schema: str | None = None, **kwargs) -> None:
        """
        Write DataFrame as table.

        Parameters
        ----------
        df : pd.DataFrame
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
        if "index" not in kwargs:
            kwargs["index"] = False
        df.to_sql(table, engine, schema=schema, **kwargs)

    ##############################
    # Utils
    ##############################

    @staticmethod
    def concat_dfs(dfs: list[pd.DataFrame]) -> pd.DataFrame:
        """
        Concatenate a list of DataFrames.

        Parameters
        ----------
        dfs : list[pd.DataFrame]
            The DataFrames to concatenate.

        Returns
        -------
        pd.DataFrame
            The concatenated DataFrame.
        """
        return pd.concat(dfs, ignore_index=True)

    @staticmethod
    def get_schema(df: pd.DataFrame) -> dict:
        """
        Get schema.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe.

        Returns
        -------
        dict
            The schema.
        """
        schema = TableSchema()
        for column_name, dtype in df.dtypes.items():
            schema.add_field(str(column_name), map_type(dtype))
        return schema.to_dict()

    @staticmethod
    def get_preview(df: pd.DataFrame) -> dict:
        """
        Get preview.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe.

        Returns
        -------
        Any
            The preview.
        """
        columns = [str(col) for col, _ in df.dtypes.items()]
        head = df.head(10).replace({np.nan: None})
        data = head.values.tolist()
        prepared_data = prepare_data(data)
        preview = prepare_preview(columns, prepared_data)
        finalizes = finalize_preview(preview, df.shape[0])
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
        return "nrows"
