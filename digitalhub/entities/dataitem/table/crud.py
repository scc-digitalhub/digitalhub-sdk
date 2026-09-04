# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from enum import Enum

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._commons.utils import build_log_name_from_source
from digitalhub.entities._processors.processors import material_processor
from digitalhub.entities.dataitem._base.crud import register_base_dataitem
from digitalhub.entities.dataitem.table.utils import (
    post_process,
    process_data_kwargs,
    process_sql_kwargs,
    read_data_sample,
)
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.generic_utils import slugify_string

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


class SourceTypes(Enum):
    DATA = "data"
    SQL = "sql"
    SOURCE = "source"


def _eval_source(
    source: SourcesOrListOfSources | None = None,
    data: Dataframe | None = None,  # type: ignore
    sql: str | None = None,
) -> str:
    if sum(value is not None for value in (source, data, sql)) != 1:
        raise ValueError("Either source, data, or sql must be provided.")
    if source is not None:
        return SourceTypes.SOURCE.value
    if data is not None:
        return SourceTypes.DATA.value
    return SourceTypes.SQL.value


def log_table(
    project: str,
    source: SourcesOrListOfSources | None = None,
    data: Dataframe | None = None,  # type: ignore
    sql: str | None = None,
    name: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    file_format: str | None = None,
    read_df_params: dict | None = None,
    engine: str | None = "pandas",
    version: str | None = None,
    schema: dict | None = None,
    **kwargs,
) -> Dataitem:
    """
    Log a dataitem table to the project.

    Parameters
    ----------
    project : str
        Project name.
    name : str, optional
        Entity name.
    source : SourcesOrListOfSources
        Dataitem location on local path. Alternative to data or sql.
    data : Dataframe
        Dataframe to log. Alternative to source or sql.
    sql : str
        SQL query to log. Alternative to source or data.
    drop_existing : bool, default=False
        Whether to drop existing entity with the same name.
    path : str, optional
        Destination path. If omitted, it is generated.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    file_format : str, optional
        Extension of the file source (parquet, csv, json, xlsx, txt).
    read_df_params : dict, optional
        Parameters to pass to the dataframe reader.
    engine : str, default="pandas"
        Dataframe engine (pandas, polars, etc.).
    version : str, optional
        Entity version.
    schema : dict, optional
        Table schema. If omitted, it is inferred from the data.
    **kwargs : dict
        Additional dataitem specification parameters.

    Returns
    -------
    Dataitem
        Created table dataitem entity with uploaded files.
    """

    kwargs = {
        key: value
        for key, value in {**kwargs, "version": version, "schema": schema}.items()
        if value is not None
    }

    data_source = _eval_source(source, data, sql)

    if data_source == SourceTypes.DATA.value and name is None:
        raise ValueError("A name is required when logging a table from a dataframe.")
    if data_source == SourceTypes.SQL.value and name is None:
        raise ValueError("A name is required when logging a table from SQL.")

    match data_source:
        case SourceTypes.SOURCE.value:
            filename = None
            if name is None:
                name = build_log_name_from_source(source)
            data = read_data_sample(
                source,
                file_format,
                read_df_params,
                engine,
            )
            kwargs = process_data_kwargs(
                project,
                name,
                data=data,
                path=path,
                source=source,
                filename=filename,
                **kwargs,
            )
            obj = material_processor.log_material_entity(
                source=source,
                project=project,
                name=name,
                kind=EntityKinds.DATAITEM_TABLE.value,
                entity_type=EntityTypes.DATAITEM.value,
                drop_existing=drop_existing,
                description=description,
                labels=labels,
                **kwargs,
            )
            return post_process(obj, data)
        case SourceTypes.DATA.value:
            filename = slugify_string(name) + f".{FileExtensions.PARQUET.value}"
            kwargs = process_data_kwargs(
                project,
                name,
                data=data,
                path=path,
                source=source,
                filename=filename,
                **kwargs,
            )
            obj = material_processor.log_dataitem_table(
                data=data,
                project=project,
                name=name,
                kind=EntityKinds.DATAITEM_TABLE.value,
                entity_type=EntityTypes.DATAITEM.value,
                drop_existing=drop_existing,
                description=description,
                labels=labels,
                **kwargs,
            )
            return post_process(obj, data)
        case SourceTypes.SQL.value:
            kwargs = process_sql_kwargs(
                name,
                sql=sql,
                path=path,
                **kwargs,
            )
            return material_processor.log_dataitem_sql(
                sql=sql,
                project=project,
                name=name,
                kind=EntityKinds.DATAITEM_TABLE.value,
                entity_type=EntityTypes.DATAITEM.value,
                drop_existing=drop_existing,
                description=description,
                labels=labels,
                **kwargs,
            )
        case _:
            raise ValueError("Invalid data source type.")


def register_table(
    project: str,
    source: SourcesOrListOfSources,
    name: str | None = None,
    uuid: str | None = None,
    version: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    embedded: bool = False,
    extensions: list[dict] | None = None,
    schema: dict | None = None,
    **kwargs,
) -> Dataitem:
    """
    Register a table dataitem entity for an existing source.

    Parameters
    ----------
    project : str
        Project name.
    source : SourcesOrListOfSources
        Path or URI of the existing table dataitem.
    name : str, optional
        Entity name. If omitted, it is inferred from ``source``.
    uuid : str, optional
        Entity identifier.
    version : str, optional
        Entity version.
    description : str, optional
        Human-readable entity description.
    labels : list[str], optional
        Entity labels.
    embedded : bool, default=False
        Whether to embed the entity specification in the project specification.
    extensions : list[dict], optional
        Entity extensions.
    schema : dict, optional
        Table schema.
    **kwargs : dict
        Additional dataitem specification parameters.

    Returns
    -------
    Dataitem
        Registered table dataitem entity.
    """
    return register_base_dataitem(
        project=project,
        source=source,
        entity_kind=EntityKinds.DATAITEM_TABLE.value,
        name=name,
        uuid=uuid,
        version=version,
        description=description,
        labels=labels,
        embedded=embedded,
        extensions=extensions,
        schema=schema,
        **kwargs,
    )
