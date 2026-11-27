# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor
from digitalhub.stores.data.api import get_store

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.protocol import MaterialProtocol
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
        obj: MaterialProtocol,
        df: Any,
        extension: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Write a DataFrame to the dataitem path and record the file in its status.

        Like ``upload()`` for a file source; saving the status is up to the caller.
        """
        store = get_store(obj.spec.path, obj.project)
        written = store.write_df(df, obj.spec.path, extension=extension, **kwargs)
        files_info = store.get_file_info(obj.spec.path, [(written, Path(obj.spec.path).name)])
        ContextEntityMaterialProcessor().update_material_files(obj, files_info)
        return written
