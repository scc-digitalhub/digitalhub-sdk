# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._processors.processors import context_processor
from digitalhub.entities.dataitem.table.utils import (
    post_process,
    process_data_kwargs,
    read_data_sample,
)
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.generic_utils import slugify_string

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


def log_table(
    project: str,
    name: str,
    source: SourcesOrListOfSources | None = None,
    data: Dataframe | None = None,  # type: ignore
    drop_existing: bool = False,
    path: str | None = None,
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
    kind : str
        Kind the object.
    source : SourcesOrListOfSources
        Dataitem location on local path. Alternative to data.
    data : Dataframe
        Dataframe to log. Alternative to source.
    drop_existing : bool
        Whether to drop existing entity with the same name.
    path : str
        Destination path of the dataitem. If not provided, it's generated.
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
    if (source is None) == (data is None):
        raise ValueError("Either source or data must be provided.")

    no_dataframe = data is None

    if data is None:
        filename = None
        data = read_data_sample(
            source,
            file_format,
            read_df_params,
            engine,
        )
    if source is None:
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

    if no_dataframe:
        obj = context_processor.log_material_entity(
            source=source,
            project=project,
            name=name,
            kind=EntityKinds.DATAITEM_TABLE.value,
            entity_type=EntityTypes.DATAITEM.value,
            drop_existing=drop_existing,
            **kwargs,
        )
    else:
        obj = context_processor.log_dataitem_table(
            data=data,
            project=project,
            name=name,
            kind=EntityKinds.DATAITEM_TABLE.value,
            entity_type=EntityTypes.DATAITEM.value,
            drop_existing=drop_existing,
            **kwargs,
        )
    return post_process(obj, data)
