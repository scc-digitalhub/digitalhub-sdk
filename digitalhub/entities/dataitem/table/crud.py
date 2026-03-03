# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from enum import Enum

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._processors.processors import context_processor
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
    if (source is None) == (data is None) == (sql is None):
        raise ValueError("Either source, data, or sql must be provided.")
    if source is not None:
        return SourceTypes.SOURCE.value
    if data is not None:
        return SourceTypes.DATA.value
    return SourceTypes.SQL.value


def log_table(
    project: str,
    name: str,
    source: SourcesOrListOfSources | None = None,
    data: Dataframe | None = None,  # type: ignore
    sql: str | None = None,
    drop_existing: bool = False,
    path: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    file_format: str | None = None,
    read_df_params: dict | None = None,
    engine: str | None = "pandas",
    **kwargs,
) -> Dataitem:
    """
    Log a dataitem table to the project.

    Parameters
    ----------
    project : str
        Project name.
    name : str
        Object name.
    source : SourcesOrListOfSources
        Dataitem location on local path. Alternative to data or sql.
    data : Dataframe
        Dataframe to log. Alternative to source or sql.
    sql : str
        SQL query to log. Alternative to source or data.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
    description : str
        Dataitem description.
    labels : list[str]
        Dataitem labels.
    file_format : str
        Extension of the file source (parquet, csv, json, xlsx, txt).
    read_df_params : dict
        Parameters to pass to the dataframe reader.
    engine : str
        Dataframe engine (pandas, polars, etc.).
    **kwargs : dict
        New dataitem spec parameters.

    Returns
    -------
    Dataitem
        Object instance.

    Examples
    --------
    >>> obj = log_dataitem(project="my-project",
    >>>                    name="my-dataitem",
    >>>                    kind="table",
    >>>                    data=df)
    """

    data_source = _eval_source(source, data, sql)

    match data_source:
        case SourceTypes.SOURCE.value:
            filename = None
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
            obj = context_processor.log_material_entity(
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
            regex_pattern = r"[^-a-z0-9_]+"
            filename = slugify_string(name, regex_pattern=regex_pattern) + f".{FileExtensions.PARQUET.value}"
            kwargs = process_data_kwargs(
                project,
                name,
                data=data,
                path=path,
                source=source,
                filename=filename,
                **kwargs,
            )
            obj = context_processor.log_dataitem_table(
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
            return context_processor.log_dataitem_sql(
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
