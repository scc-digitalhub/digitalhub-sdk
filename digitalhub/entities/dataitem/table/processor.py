# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.stores.data.api import get_store

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.table.entity import DataitemTable


class DataitemTableProcessor:
    """Read and write the DataFrame of a table dataitem."""

    def read_df(
        self,
        obj: DataitemTable,
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Read the dataitem path as a DataFrame."""
        return get_store(obj.spec.path, obj.project).read_df(obj.spec.path, file_format, engine, **kwargs)

    def write_df(
        self,
        obj: DataitemTable,
        df: Any,
        extension: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Write a DataFrame to the dataitem path."""
        return get_store(obj.spec.path, obj.project).write_df(df, obj.spec.path, extension=extension, **kwargs)
