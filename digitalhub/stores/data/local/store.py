# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

from digitalhub.stores.data._base.store import Store
from digitalhub.stores.readers.data.api import get_reader_by_object
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.file_utils import get_file_info_from_local
from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


class LocalStore(Store):
    """
    Local store class. It implements the Store interface and provides methods to fetch and persist
    artifacts on local filesystem based storage.
    """

    ##############################
    # I/O methods
    ##############################

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Method to get file metadata.
        """
        return [get_file_info_from_local(path, src_path) for path, src_path in paths]

    ##############################
    # Datastore methods
    ##############################

    def read_df(
        self,
        path: SourcesOrListOfSources,
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Dataframe:  # type: ignore
        """
        Read DataFrame from path.
        """
        reader = self._get_reader(engine)

        dfs = []
        if isinstance(path, list):
            for p in path:
                extension = self._get_extension(file_format, p)
                dfs.append(reader.read_df(p, extension, **kwargs))
        elif Path(path).is_dir():
            paths = [p for p in Path(path).iterdir() if p.is_file() and not p.name.startswith(".")]
            for p in paths:
                extension = self._get_extension(file_format, str(p))
                dfs.append(reader.read_df(str(p), extension, **kwargs))
        else:
            extension = self._get_extension(file_format, path)
            dfs.append(reader.read_df(path, extension, **kwargs))

        if not dfs:
            raise StoreError(f"No readable data files found in '{path}'.")
        if len(dfs) == 1:
            return dfs[0]

        return reader.concat_dfs(dfs)

    def write_df(self, df: Any, dst: str, extension: str | None = None, **kwargs) -> str:
        """
        Method to write a dataframe to a file. Kwargs are passed to df.to_parquet().
        If destination is not provided, the dataframe is written to the default
        store path with generated name.
        """
        self._check_local_dst(dst)
        reader = get_reader_by_object(df)
        reader.write_df(df, dst, extension=extension, **kwargs)
        return dst
