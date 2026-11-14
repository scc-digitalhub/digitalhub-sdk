# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.data._base.store import Store
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


class RemoteStore(Store):
    """
    HTTP store class. It implements the Store interface and provides methods to fetch
    artifacts from remote HTTP based storage.
    """

    ##############################
    # I/O methods
    ##############################

    def download(
        self,
        root: str,
        dst: Path,
        overwrite: bool = False,
    ) -> str:
        """
        Download artifacts from storage.
        """
        # Handle destination
        if dst is None:
            dst = self._build_temp()
        else:
            self._check_local_dst(str(dst))

        if dst.suffix == "":
            dst = dst / "data.file"

        self._check_overwrite(dst, overwrite)
        self._build_path(dst)

        return self._download_file(root, dst, overwrite)

    def upload(
        self,
        src: SourcesOrListOfSources,
        dst: str,
        keep_dir_structure: bool = False,
    ) -> list[tuple[str, str]]:
        """
        Upload an artifact to storage.
        """
        raise StoreError("Remote HTTP store does not support upload.")

    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Get file information from HTTP(s) storage.
        """
        return []

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
        extension = self._head_extension(path, file_format)
        return reader.read_df(path, extension, **kwargs)

    def write_df(self, df: Any, dst: str, extension: str | None = None, **kwargs) -> str:
        """
        Method to write a dataframe to a file. Note that this method is not implemented
        since the remote store is not meant to write dataframes.
        """
        raise NotImplementedError("Remote store does not support write_df.")

    ##############################
    # Helper methods
    ##############################

    @staticmethod
    def _check_head(src) -> None:
        """
        Check if the source exists.
        """
        r = requests.head(src, timeout=get_client_config().http_timeout)
        r.raise_for_status()

    def _download_file(self, url: str, dst: Path, overwrite: bool) -> str:
        """
        Method to download a file from a given url.
        """
        with requests.get(
            url,
            stream=True,
            timeout=get_client_config().http_timeout,
            allow_redirects=True,
        ) as r:
            r.raise_for_status()
            with open(dst, "wb") as f:
                f.writelines(r.iter_content(chunk_size=8192))
        return str(dst)

    def _head_extension(self, url: str, file_format: str | None = None) -> str:
        """
        Method to get the extension of a file from a given url.
        """
        if file_format is not None:
            return file_format

        r = requests.head(url, timeout=get_client_config().http_timeout)
        r.raise_for_status()
        content_type = r.headers["content-type"]
        if "text" in content_type:
            return "csv"
        raise ValueError("Content type not supported.")
