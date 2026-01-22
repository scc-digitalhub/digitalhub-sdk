# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.readers.data.factory import factory
from digitalhub.utils.exceptions import ReaderError

if typing.TYPE_CHECKING:
    from digitalhub.stores.readers.data._base.reader import DataframeReader
    from digitalhub.utils.types import Dataframe


def get_reader_by_engine(engine: str | None = None) -> DataframeReader:
    """
    Get Dataframe reader.

    Parameters
    ----------
    engine : str
        Dataframe engine (pandas, polars, etc.).

    Returns
    -------
    DataframeReader
        Reader object.
    """
    if engine is None:
        engine = factory.get_default()
    try:
        return factory.build(engine=engine)
    except KeyError:
        engines = factory.list_supported_engines()
        msg = f"Unsupported dataframe engine: '{engine}'. Supported engines: {engines}"
        raise ReaderError(msg)


def get_reader_by_object(obj: Dataframe) -> DataframeReader:  # type: ignore
    """
    Get Dataframe reader by object.

    Parameters
    ----------
    obj : Dataframe
        Dataframe object.

    Returns
    -------
    DataframeReader
        Reader object.
    """
    try:
        return factory.build(dataframe=obj)
    except KeyError:
        types = factory.list_supported_engines()
        msg = f"Unsupported dataframe type: '{obj}'. Supported dataframes: {types}"
        raise ReaderError(msg)


def get_supported_engines() -> list[str]:
    """
    Get supported engines.

    Returns
    -------
    list
        List of supported engines.
    """
    return factory.list_supported_engines()


def get_supported_dataframes() -> list[Dataframe]:  # type: ignore
    """
    Get supported dataframes.

    Returns
    -------
    list[Dataframe]
        List of supported dataframes.
    """
    return factory.list_supported_dataframes()
