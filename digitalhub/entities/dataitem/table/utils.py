# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.utils import build_log_path_from_filename, build_log_path_from_source
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.stores.data.api import get_store
from digitalhub.stores.readers.data.api import get_reader_by_engine, get_reader_by_object
from digitalhub.utils.file_utils import eval_local_source

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


def read_data_sample(
    source: SourcesOrListOfSources,
    file_format: str | None = None,
    read_df_params: dict | None = None,
    engine: str | None = None,
) -> Dataframe:  # type: ignore
    """
    Evaluate and load data from source or return provided data.

    Parameters
    ----------
    source : SourcesOrListOfSources
        The source specification(s) to load data from.
    file_format : str
        The file format specification for reading the source (e.g., 'parquet', 'csv').
    engine : str
        The engine to use for reading the data (e.g., 'pandas', 'polars').

    Returns
    -------
    Dataframe
        Loaded data object.
    """
    eval_local_source(source)
    if read_df_params is None or not isinstance(read_df_params, dict):
        read_df_params = {}
    reader = get_reader_by_engine(engine)
    read_df_params[reader.get_limit_arg_name()] = 10
    return get_store(source).read_df(
        source,
        file_format=file_format,
        engine=engine,
        **read_df_params,
    )


def process_data_kwargs(
    project: str,
    name: str,
    data: Dataframe,  # type: ignore
    path: str | None = None,
    source: SourcesOrListOfSources | None = None,
    filename: str | None = None,
    **kwargs,
) -> dict:
    """
    Process and enhance specification parameters for dataitem creation.

    Parameters
    ----------
    project : str
        The name of the project.
    name : str
        The name of the dataitem entity.
    kind : str
        The kind of dataitem being created (e.g., 'table').
    path : str
        The destination path for the dataitem entity.
        If None, a path will be automatically generated.
    data : Dataframe
        The data object for schema extraction and processing.
        Used as an alternative to source for table dataitems.
    source
    **kwargs : dict
        Additional specification parameters to be processed
        and passed to the dataitem creation.

    Returns
    -------
    dict
        The enhanced specification parameters for dataitem creation.
    """
    if (source is None) == (filename is None):
        raise ValueError("Either source or filename must be provided.")
    if source is None:
        fn = build_log_path_from_filename
        arg = filename
    else:
        fn = build_log_path_from_source
        arg = source

    if path is None:
        uuid = build_uuid()
        kwargs["uuid"] = uuid
        kwargs["path"] = fn(project, EntityTypes.DATAITEM.value, name, uuid, arg)

    kwargs["schema"] = get_reader_by_object(data).get_schema(data)
    return kwargs


def post_process(
    obj: Dataitem,
    data: Dataframe,  # type: ignore
) -> Dataitem:
    """
    Post-process dataitem object with additional metadata and previews.

    Enhances the dataitem object with additional information extracted
    from the data. For table dataitems, generates and stores a data
    preview in the object's status.

    Parameters
    ----------
    obj : Dataitem
        The dataitem object to post-process and enhance.
    data : Dataframe
        The data object used to generate previews and extract
        additional metadata information.

    Returns
    -------
    Dataitem
        The enhanced dataitem object with updated status information
        and saved changes.
    """
    reader = get_reader_by_object(data)
    obj.status.preview = reader.get_preview(data)
    obj.save(update=True)
    return obj
