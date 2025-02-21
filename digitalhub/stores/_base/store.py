from __future__ import annotations

import typing
from abc import abstractmethod
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from digitalhub.readers.data.api import get_reader_by_engine
from digitalhub.utils.exceptions import StoreError
from digitalhub.utils.uri_utils import has_local_scheme

if typing.TYPE_CHECKING:
    from digitalhub.readers.data._base.reader import DataframeReader


class Store:
    """
    Store abstract class.
    """

    ##############################
    # I/O methods
    ##############################

    @abstractmethod
    def download(
        self,
        root: str,
        dst: Path,
        src: list[str],
        overwrite: bool = False,
    ) -> str:
        """
        Method to download artifact from storage.
        """

    @abstractmethod
    def upload(self, src: str | list[str], dst: str) -> list[tuple[str, str]]:
        """
        Method to upload artifact to storage.
        """

    @abstractmethod
    def get_file_info(
        self,
        root: str,
        paths: list[tuple[str, str]],
    ) -> list[dict]:
        """
        Method to get file metadata.
        """

    ##############################
    # Datastore methods
    ##############################

    @abstractmethod
    def read_df(
        self,
        path: str | list[str],
        file_format: str | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Any:
        """
        Read DataFrame from path.
        """

    @abstractmethod
    def query(
        self,
        query: str,
        engine: str | None = None,
    ) -> Any:
        """
        Query data from database.
        """

    @abstractmethod
    def write_df(self, df: Any, dst: str, extension: str | None = None, **kwargs) -> str:
        """
        Write DataFrame as parquet or csv.
        """

    ##############################
    # Helpers methods
    ##############################

    def _check_local_src(self, src: str) -> None:
        """
        Check if the source path is local.

        Parameters
        ----------
        src : str
            The source path.

        Returns
        -------
        None

        Raises
        ------
        StoreError
            If the source is not a local path.
        """
        if not has_local_scheme(src):
            raise StoreError(f"Source '{src}' is not a local path.")

    def _check_local_dst(self, dst: str) -> None:
        """
        Check if the destination path is local.

        Parameters
        ----------
        dst : str
            The destination path.

        Returns
        -------
        None

        Raises
        ------
        StoreError
            If the destination is not a local path.
        """
        if not has_local_scheme(dst):
            raise StoreError(f"Destination '{dst}' is not a local path.")

    def _check_overwrite(self, dst: Path, overwrite: bool) -> None:
        """
        Check if destination path exists for overwrite.

        Parameters
        ----------
        dst : Path
            Destination path as filename.
        overwrite : bool
            Specify if overwrite an existing file.

        Returns
        -------
        None

        Raises
        ------
        StoreError
            If destination path exists and overwrite is False.
        """
        if dst.exists() and not overwrite:
            raise StoreError(f"Destination {str(dst)} already exists.")

    @staticmethod
    def _build_path(path: str | Path) -> None:
        """
        Get path from store path and path.

        Parameters
        ----------
        path : str
            The path to build.

        Returns
        -------
        None
        """
        if not isinstance(path, Path):
            path = Path(path)
        if path.suffix != "":
            path = path.parent
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _build_temp() -> Path:
        """
        Build a temporary path.

        Returns
        -------
        Path
            Temporary path.
        """
        tmpdir = mkdtemp()
        return Path(tmpdir)

    @staticmethod
    def _get_reader(engine: str | None = None) -> DataframeReader:
        """
        Get Dataframe reader.

        Parameters
        ----------
        engine : str
            Dataframe engine (pandas, polars, etc.).

        Returns
        -------
        Any
            Reader object.
        """
        return get_reader_by_engine(engine)

    @staticmethod
    def _get_extension(extension: str | None = None, path: str | None = None) -> str:
        """
        Get extension from path.

        Parameters
        ----------
        extension : str
            The extension to get.
        path : str
            The path to get the extension from.

        Returns
        -------
        str
            The extension.
        """
        if extension is not None:
            return extension
        if path is not None:
            return Path(path).suffix.removeprefix(".")
        raise ValueError("Extension or path must be provided.")
