# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.dataitem.croissant.utils import (
    get_croissant_dataset,
    get_files_from_croissant,
    get_mappings_from_croissant,
)
from digitalhub.stores.data.api import get_store
from digitalhub.utils.uri_utils import has_s3_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.croissant.spec import DataitemSpecCroissant
    from digitalhub.entities.dataitem.croissant.status import DataitemStatusCroissant


class DataitemCroissant(Dataitem):
    """
    DataitemCroissant class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: DataitemSpecCroissant
        self.status: DataitemStatusCroissant

    @refresh_decorator
    def as_dataset(self, overwrite: bool = False) -> Any:
        """
        Get the Croissant Dataset object from the Dataitem.

        Parameters
        ----------
        overwrite : bool
            Flag to indicate overwrite of local files.

        Returns
        -------
        mlcroissant.Dataset
            Croissant Dataset object.
        """
        metadata_json_path = self._get_metadata_json()
        dtst = get_croissant_dataset(metadata_json_path)
        self._collect_local_data(dtst, metadata_json_path, overwrite=overwrite)
        mapping = self._map_files_filepaths(dtst)
        return get_croissant_dataset(metadata_json_path, mapping=mapping)

    def _get_metadata_json(self) -> str:
        """
        Get the metadata JSON croissant file.

        Returns
        -------
        str
            Metadata file path.
        """
        if has_s3_scheme(self.spec.path):
            store = get_store(self.spec.path)
            return store.download(
                self.spec.path + "metadata.json",
                self._context().root / self.ENTITY_TYPE,
                overwrite=True,
            )
        return self.download(overwrite=True)

    def _collect_local_data(
        self,
        dataset: Any,
        metadata_path: str,
        overwrite: bool = False,
    ) -> None:
        """
        Collect local data files from Croissant metadata.

        Parameters
        ----------
        dataset : mlcroissant.Dataset
            Croissant Dataset object.
        metadata_path : str
            Path to the metadata JSON file.
        overwrite : bool
            Flag to indicate overwrite of local files.
        """
        if not has_s3_scheme(self.spec.path):
            return
        local_files = get_files_from_croissant(dataset, metadata_path)
        store = get_store(self.spec.path)
        for file_path in local_files:
            key = self.spec.path + str(Path(file_path))
            store.download(
                key,
                self._context().root / self.ENTITY_TYPE / Path(file_path),
                overwrite=overwrite,
            )

    def _map_files_filepaths(self, dataset: Any) -> dict | None:
        """
        Map file paths from Croissant metadata to local paths.

        Parameters
        ----------
        dataset : Any
            Croissant Dataset object.

        Returns
        -------
        dict | None
            Mapping of file paths.
        """
        if not has_s3_scheme(self.spec.path):
            return
        download_root = self._context().root / self.ENTITY_TYPE
        return get_mappings_from_croissant(dataset, self._get_metadata_json(), download_root)
