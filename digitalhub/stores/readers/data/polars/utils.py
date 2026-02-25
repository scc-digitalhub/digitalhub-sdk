# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Any, Callable

import polars as pl

from digitalhub.utils.enums import DataTypes, FileExtensions
from digitalhub.utils.generic_utils import CustomJsonEncoder


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


def serialize_deserialize_preview(preview: dict) -> dict:
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


def map_read_function(extension: str) -> Callable:
    """
    Map file extension to Polars read function.

    Parameters
    ----------
    extension : str
        The file extension.

    Returns
    -------
    Callable
        The Polars read function.
    """
    match extension:
        case FileExtensions.CSV.value:
            return pl.read_csv
        case FileExtensions.PARQUET.value:
            return pl.read_parquet
        case FileExtensions.JSON.value:
            return pl.read_json
        case FileExtensions.EXCEL.value | FileExtensions.EXCEL_OLD.value:
            return pl.read_excel
        case FileExtensions.TXT.value | FileExtensions.FILE.value:
            return pl.read_csv
        case _:
            raise ValueError(f"Unsupported file extension: {extension}")


def map_write_function(extension: str) -> Callable:
    """
    Map file extension to Polars write function.

    Parameters
    ----------
    extension : str
        The file extension.

    Returns
    -------
    Callable
        The Polars write function.
    """
    match extension:
        case FileExtensions.CSV.value:
            return pl.DataFrame.write_csv
        case FileExtensions.PARQUET.value:
            return pl.DataFrame.write_parquet
        case _:
            raise ValueError(f"Unsupported file extension: {extension}")


def map_type(dtype: pl.DataType) -> str:
    """
    Map Polars data type to generic data type.

    Parameters
    ----------
    dtype : pl.DataType
        The Polars data type.

    Returns
    -------
    str
        The mapped data type.
    """
    match dtype:
        case pl.Int8 | pl.Int16 | pl.Int32 | pl.Int64 | pl.UInt8 | pl.UInt16 | pl.UInt32 | pl.UInt64:
            return DataTypes.INTEGER.value
        case pl.Float32 | pl.Float64 | pl.Decimal:
            return DataTypes.NUMBER.value
        case pl.Boolean:
            return DataTypes.BOOLEAN.value
        case pl.Date | pl.Datetime:
            return DataTypes.DATETIME.value
        case pl.Utf8 | pl.Object:
            return DataTypes.STRING.value
        case _:
            return DataTypes.ANY.value
