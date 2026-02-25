# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Any, Callable

import pandas as pd

from digitalhub.utils.enums import DataTypes, FileExtensions
from digitalhub.utils.generic_utils import CustomJsonEncoder


class PandasJsonEncoder(CustomJsonEncoder):
    """
    JSON pd.Timestamp to ISO format serializer.
    """

    def default(self, obj: Any) -> Any:
        """
        Pandas datetime to ISO format serializer.

        Parameters
        ----------
        obj : Any
            The object to serialize.

        Returns
        -------
        Any
            The serialized object.
        """
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
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
    return json.loads(json.dumps(preview, cls=PandasJsonEncoder))


def map_read_function(extension: str) -> Callable:
    """
    Map file extension to Pandas read function.

    Parameters
    ----------
    extension : str
        The file extension.

    Returns
    -------
    Callable
        The Pandas read function.
    """
    match extension:
        case FileExtensions.CSV.value:
            return pd.read_csv
        case FileExtensions.PARQUET.value:
            return pd.read_parquet
        case FileExtensions.JSON.value:
            return pd.read_json
        case FileExtensions.EXCEL.value | FileExtensions.EXCEL_OLD.value:
            return pd.read_excel
        case FileExtensions.TXT.value | FileExtensions.FILE.value:
            return pd.read_csv
        case _:
            raise ValueError(f"Unsupported file extension: {extension}")


def map_write_function(extension: str) -> Callable:
    """
    Map file extension to Pandas write function.

    Parameters
    ----------
    extension : str
        The file extension.

    Returns
    -------
    Callable
        The Pandas write function.
    """
    match extension:
        case FileExtensions.CSV.value:
            return pd.DataFrame.to_csv
        case FileExtensions.PARQUET.value:
            return pd.DataFrame.to_parquet
        case _:
            raise ValueError(f"Unsupported file extension: {extension}")


def map_type(dtype: Any) -> str:
    """
    Map Pandas data type to generic data type.

    Parameters
    ----------
    dtype : Any
        The Pandas data type.

    Returns
    -------
    str
        The mapped data type.
    """
    match True:
        case _ if pd.api.types.is_integer_dtype(dtype):
            return DataTypes.INTEGER.value
        case _ if pd.api.types.is_float_dtype(dtype):
            return DataTypes.NUMBER.value
        case _ if pd.api.types.is_bool_dtype(dtype):
            return DataTypes.BOOLEAN.value
        case _ if pd.api.types.is_string_dtype(dtype):
            return DataTypes.STRING.value
        case _ if pd.api.types.is_datetime64_any_dtype(dtype):
            return DataTypes.DATETIME.value
        case _:
            return DataTypes.ANY.value
