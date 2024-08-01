from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from digitalhub_core.stores.builder import get_store
from digitalhub_core.utils.uri_utils import check_local_path
from digitalhub_data.datastores.builder import get_datastore
from digitalhub_data.entities.dataitem.entity._base import Dataitem


class DataitemTable(Dataitem):

    """
    Table dataitem.
    """

    def as_df(
        self,
        file_format: str | None = None,
        clean_tmp_path: bool = True,
        **kwargs,
    ) -> Any:
        """
        Read dataitem as a DataFrame from spec.path. If the dataitem is not local,
        it will be downloaded to a temporary folder. If clean_tmp_path is True,
        the temporary folder will be deleted after the method is executed.

        Parameters
        ----------
        file_format : str
            Format of the file. (Supported csv and parquet).
        clean_tmp_path : bool
            If True, the temporary folder will be deleted.
        **kwargs : dict
            Keyword arguments passed to the read_df function.

        Returns
        -------
        Any
            DataFrame.
        """
        try:
            if check_local_path(self.spec.path):
                tmp_dir = None
            else:
                tmp_dir = self._context().tmp_dir / "data"

            # Check file format and get dataitem as DataFrame
            store = get_store(self.spec.path)
            paths = self._get_paths()
            download_paths = store.download(paths, dst=str(tmp_dir), overwrite=True)

            if not download_paths:
                raise RuntimeError(f"No file found in {self.spec.path}.")

            path = download_paths[0]
            extension = self._get_extension(path, file_format)
            datastore = get_datastore(path)
            return datastore.read_df(download_paths, extension, **kwargs)

        except Exception as e:
            raise e

        finally:
            # Delete tmp folder
            self._clean_tmp_path(tmp_dir, clean_tmp_path)

    def write_df(
        self,
        df: Any,
        extension: str | None = None,
        **kwargs,
    ) -> str:
        """
        Write DataFrame as parquet/csv/table into dataitem path.

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
        datastore = get_datastore(self.spec.path)
        return datastore.write_df(df, self.spec.path, extension=extension, **kwargs)

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
