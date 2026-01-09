# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Union

_dataframe_types = []

try:
    from pandas import DataFrame as PandasDataFrame

    _dataframe_types.append(PandasDataFrame)
except ImportError:
    pass

try:
    from polars import DataFrame as PolarsDataFrame

    _dataframe_types.append(PolarsDataFrame)
except ImportError:
    pass

SourcesOrListOfSources = str | list[str]

Dataframe = Union[tuple(_dataframe_types)]  # type: ignore
