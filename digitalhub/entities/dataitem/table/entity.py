# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
import typing
from pathlib import Path
from typing import Any

from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.stores.data.api import get_store
from digitalhub.utils.uri_utils import has_sql_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.dataitem.table.spec import DataitemSpecTable
    from digitalhub.entities.dataitem.table.status import DataitemStatusTable


class DataitemTable(Dataitem):
    """
    DataitemTable class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: DataitemSpecTable,
        status: DataitemStatusTable,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: DataitemSpecTable
        self.status: DataitemStatusTable

        self._query: str | None = None

    def query(self, query: str) -> DataitemTable:
        """
        Set query to execute.

        Parameters
        ----------
        query : str
            Query to execute.

        Returns
        -------
        DataitemTable
            Self object.
        """
        # to remove in future
        if not has_sql_scheme(self.spec.path):
            raise ValueError(
                f"Dataitem path is not a SQL scheme: {self.spec.path}",
                " Query can be made only on a SQL scheme.",
            )
        self._query = query
        return self

    def as_df(
        self,
        file_format: str | None = None,
        engine: str | None = "pandas",
        **kwargs,
    ) -> Any:
        """
        Read dataitem file (csv or parquet) as a DataFrame from spec.path.
        It's possible to pass additional arguments to the this function. These
        keyword arguments will be passed to the DataFrame reader function such as
        pandas's read_csv or read_parquet.

        Parameters
        ----------
        file_format : str
            Format of the file to read. By default, it will be inferred from
            the extension of the file.
        engine : str
            Dataframe framework, by default pandas.
        **kwargs : dict
            Keyword arguments passed to the read_df function.

        Returns
        -------
        Any
            DataFrame.
        """
        if self._query is not None:
            df = get_store(self.project, self.spec.path).query(
                self._query,
                self.spec.path,
                engine,
            )
            self._query = None
            return df
        return get_store(self.project, self.spec.path).read_df(
            self.spec.path,
            file_format,
            engine,
            **kwargs,
        )

    def write_df(
        self,
        df: Any,
        extension: str | None = None,
        **kwargs,
    ) -> str:
        """
        Write DataFrame as parquet/csv/table into dataitem spec.path.
        keyword arguments will be passed to the DataFrame reader function such as
        pandas's to_csv or to_parquet.

        Parameters
        ----------
        df : Any
            DataFrame to write.
        extension : str
            Extension of the file.
        **kwargs : dict
            Keyword arguments passed to the write_df function.

        Returns
        -------
        str
            Path to the written dataframe.
        """
        return get_store(self.project, self.spec.path).write_df(
            df,
            self.spec.path,
            extension=extension,
            **kwargs,
        )

    @staticmethod
    def _clean_tmp_path(pth: Path | None, clean: bool) -> None:
        """
        Clean temporary path.

        Parameters
        ----------
        pth : Path | None
            Path to clean.
        clean : bool
            If True, the path will be cleaned.

        Returns
        -------
        None
        """
        if pth is not None and clean:
            shutil.rmtree(pth)
