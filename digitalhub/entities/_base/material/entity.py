# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import State
from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities._processors.processors import context_processor
from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import BackendError, EntityError, EntityErrorFileNotFound, StoreError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.material.spec import MaterialSpec
    from digitalhub.entities._base.material.status import MaterialStatus
    from digitalhub.entities._base.metadata.entity import Metadata

logger = get_logger(__name__)
MAX_FILES_IN_STATUS = 100


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
        self.status.state = State.UPLOADING.value
        self.save(update=True)

        store = get_store(self.spec.path)
        error: Exception | None = None
        try:
            paths = store.upload(
                source,
                self.spec.path,
                keep_dir_structure=keep_dir_structure,
            )

            files_info = store.get_file_info(self.spec.path, paths)
            self._update_files_info(files_info)
            uploaded = True
            msg = None
        except FileNotFoundError as e:
            uploaded = False
            msg = f"Upload failed: {e}. Please verify that the specified source files are correct and exist."
            exception = EntityErrorFileNotFound
            error = e
        except (StoreError, OSError, ValueError, NotImplementedError) as e:
            uploaded = False
            msg = f"Upload failed: {e}"
            exception = EntityError
            error = e

        self.status.message = msg

        if uploaded:
            self.status.state = State.READY.value
            self.save(update=True)
            return

        self.status.state = State.ERROR.value
        self.save(update=True)
        raise exception(msg) from error

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
        if self._has_files_info():
            files_info = self._get_files_info()
            if files_info:
                return files_info
            if self.status.files:
                return self.status.files
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
        if len(files_info) <= MAX_FILES_IN_STATUS:
            self.status.files = files_info
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

        self.status.files = []
        self.save(update=True)
        context_processor.update_files_info(
            self.project,
            self.ENTITY_TYPE,
            self.id,
            files_info,
        )

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
