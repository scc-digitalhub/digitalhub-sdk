# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities._processors.processors import context_processor
from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.material.spec import MaterialSpec
    from digitalhub.entities._base.material.status import MaterialStatus
    from digitalhub.entities._base.metadata.entity import Metadata

logger = get_logger(__name__)


class MaterialEntity(VersionedEntity):
    """
    A class representing an entity that can be materialized
    as file(s).
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: MaterialSpec,
        status: MaterialStatus,
        extensions: list[dict],
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)
        self.spec: MaterialSpec
        self.status: MaterialStatus
        self.extensions: list[dict] = extensions

        # Attributes to be included in __repr__
        self._obj_attr.extend(["extensions"])

    ##############################
    # I/O Methods
    ##############################

    @refresh_decorator
    def as_file(self) -> list[str]:
        """
        Get object as file(s). It downloads the object from storage in
        a temporary folder and returns the list of downloaded files paths.

        Returns
        -------
        list[str]
            List of file paths.
        """
        store = get_store(self.spec.path)
        dst = store._build_temp()
        return store.download(self.spec.path, dst=dst)

    @refresh_decorator
    def download(
        self,
        destination: str | None = None,
        overwrite: bool = False,
    ) -> str:
        """
        This function downloads one or more file from storage on local
        machine from spec.path.
        The files are downloaded into a destination folder. If the destination
        is not specified, it will set by default under the context path
        as '<ctx-root>/<entity_type>', e.g. './dataitem'.
        The overwrite flag allows to overwrite existing file(s) in the
        destination folder.

        Parameters
        ----------
        destination : str
            Destination path as filename or directory.
        overwrite : bool
            Specify if overwrite existing file(s). If file(s) already
            exist and overwrite is False, it will raise an error.

        Returns
        -------
        str
            Download path.

        Examples
        --------
        Download a single file:

        >>> path = entity.download()
        >>> print(path)
        dataitem/data.csv
        """
        store = get_store(self.spec.path)

        if destination is None:
            dst = self._context().root / self.ENTITY_TYPE
        else:
            dst = Path(destination)

        return store.download(self.spec.path, dst, overwrite=overwrite)

    @refresh_decorator
    def upload(
        self,
        source: SourcesOrListOfSources,
        keep_dir_structure: bool = False,
    ) -> None:
        """
        Upload object from given local path to spec path destination.
        Source must be a local path. If the path is a folder, destination
        path (object's spec path) must be a folder or a partition ending
        with '/' (s3).

        Parameters
        ----------
        source : str | list[str]
            Local filepath, directory or list of filepaths.
        keep_dir_structure : bool
            Flag to indicate whether to keep the directory structure when uploading
            from a list of files.

        Examples
        --------
        Upload a single file:

        >>> entity.spec.path = "s3://bucket/data.csv"
        >>> entity.upload("./data.csv")

        Upload a folder:
        >>> entity.spec.path = "s3://bucket/data/"
        >>> entity.upload("./data")
        """
        # Get store and upload object
        store = get_store(self.spec.path)
        paths = store.upload(
            source,
            self.spec.path,
            keep_dir_structure=keep_dir_structure,
        )

        # Update files info
        files_info = store.get_file_info(self.spec.path, paths)
        self._update_files_info(files_info)

    ##############################
    #  Public Helpers
    ##############################

    @property
    def files(self) -> list[dict]:
        """
        Get files info list.

        Returns
        -------
        list[dict]
            Files info list.
        """
        if self.status.files:
            return self.status.files
        elif self._has_files_info():
            return self._get_files_info()
        return []

    def _has_files_info(self) -> bool:
        """
        Check if the entity has files info.

        Returns
        -------
        bool
            True if the entity has files info, False otherwise.
        """
        return self.status.files is not None

    def get_file_paths(self) -> list:
        """
        Get the paths of the files in the status.

        Returns
        -------
        list
            Paths of the files in the status.
        """
        return [f.get("path") for f in self.files]

    ##############################
    #  Private Helpers
    ##############################

    def _update_files_info(self, files_info: list[dict] | None = None) -> None:
        """
        Update files info through the dedicated backend endpoint.

        Parameters
        ----------
        files_info : list[dict] | None
            Files info.
        """
        if files_info is None:
            return
        self._log_files_info(files_info)

    def _log_files_info(self, files_info: list[dict]) -> None:
        """
        Log files info through the dedicated backend endpoint.

        Parameters
        ----------
        files_info : list[dict]
            Files info to log.
        """
        if not files_info:
            return

        if not self._has_files_info():
            self.status.files = []
            self.save(update=True)
            current_files = []
            migrate_status_files = False
        else:
            if self.status.files:
                self.refresh()
            current_files = self.files
            migrate_status_files = bool(self.status.files)

        updated_files = self._merge_files_info(current_files, files_info)
        context_processor.update_files_info(
            self.project,
            self.ENTITY_TYPE,
            self.id,
            updated_files,
        )

        if migrate_status_files:
            self.status.files = []
            self.save(update=True)

    @staticmethod
    def _merge_files_info(current_files: list[dict], new_files: list[dict]) -> list[dict]:
        """
        Merge files info by path, keeping the latest value for duplicates.

        Parameters
        ----------
        current_files : list[dict]
            Current files info.
        new_files : list[dict]
            New files info to merge.

        Returns
        -------
        list[dict]
            Merged files info.
        """
        merged_files = list(current_files)
        path_index = {
            file_info["path"]: index
            for index, file_info in enumerate(merged_files)
            if file_info.get("path") is not None
        }

        for file_info in new_files:
            path = file_info.get("path")
            if path is None or path not in path_index:
                if path is not None:
                    path_index[path] = len(merged_files)
                merged_files.append(file_info)
                continue

            merged_files[path_index[path]] = file_info

        return merged_files

    def _get_files_info(self) -> list[dict]:
        """
        Get files info from backend.
        """
        try:
            return context_processor.read_files_info(
                project=self.project,
                entity_type=self.ENTITY_TYPE,
                entity_id=self.id,
            )
        except BackendError:
            logger.debug(
                f"Could not retrieve files info for entity '{self.id}' from backend.",
                exc_info=True,
            )
            return []
