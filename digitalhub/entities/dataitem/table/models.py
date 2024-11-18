from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FieldType(Enum):
    """
    Field type enum.
    """

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    YEAR = "year"
    YEARMONTH = "yearmonth"
    DURATION = "duration"
    GEOPOINT = "geopoint"
    GEOJSON = "geojson"
    ANY = "any"


class TableSchemaFieldEntry(BaseModel):
    """
    Table schema field entry model.
    """

    model_config = ConfigDict(use_enum_values=True)

    name: str
    """Field name."""

    type_: FieldType = Field(alias="type")
    """Field type."""

    title: str = None
    """Field title."""

    format_: str = Field(default=None, alias="format")
    """Field format."""

    example: str = None
    """Field example."""

    description: str = None
    """Field description."""


class TableSchema(BaseModel):
    """
    Table schema model.
    """

    fields: list[TableSchemaFieldEntry]
