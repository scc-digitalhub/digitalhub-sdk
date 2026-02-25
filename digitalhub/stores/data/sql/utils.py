# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.utils.data_utils import TableSchema
from digitalhub.utils.enums import DataTypes

if typing.TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import ReflectedColumn


def _map_sql_type(col_type: str) -> str:
    """
    Map SQL column types to generic types.

    Parameters
    ----------
    col_type : str
        The SQL column type as a string.

    Returns
    -------
    str
        Type mapped.
    """
    col_type = col_type.lower()
    match True:
        case _ if any(t in col_type for t in ["int", "serial"]):
            return DataTypes.INTEGER.value
        case _ if any(t in col_type for t in ["float", "double", "real", "numeric", "decimal"]):
            return DataTypes.NUMBER.value
        case _ if any(t in col_type for t in ["bool"]):
            return DataTypes.BOOLEAN.value
        case _ if any(t in col_type for t in ["date", "time"]):
            return DataTypes.DATETIME.value
        case _ if any(t in col_type for t in ["char", "text", "json", "uuid", "enum", "varchar"]):
            return DataTypes.STRING.value
        case _:
            return DataTypes.ANY.value


def get_schema_from_columns(columns: list[ReflectedColumn]) -> dict:
    """
    Get schema from SQL table columns.

    Parameters
    ----------
    columns : list
        The list of columns as returned by SQLAlchemy inspector.

    Returns
    -------
    dict
        The schema as a dictionary with column names as keys and mapped types as values.
    """
    schema = TableSchema()
    for col in columns:
        schema.add_field(str(col.get("name")), _map_sql_type(str(col.get("type"))))
    return schema.to_dict()
