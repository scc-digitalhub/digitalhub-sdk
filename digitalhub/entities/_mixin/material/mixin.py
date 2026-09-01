# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import ClassVar

from digitalhub.entities._commons.enums import State
from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities._processors.processors import material_processor
from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import BackendError, EntityError, EntityErrorFileNotFound, StoreError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities._mixin.material.status import MaterialStatus

logger = get_logger(__name__)
MAX_FILES_IN_STATUS = 100


class MaterialMixin:
    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str
    spec: MaterialSpec
    status: MaterialStatus
    extensions: list[dict]

    def _init_material_extensions(self, extensions: list[dict] | None = None) -> None:
        self.extensions = extensions if extensions is not None else []

    @refresh_decorator
    def as_file(self) -> list[str]:
        """Download the entity's files to a temporary local directory.

        Returns
        -------
        list[str]
            Paths to the downloaded files.
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
        """Download the entity's files to a local destination.

        Parameters
        ----------
        destination : str, optional
            Local destination directory. If omitted, use the project context
            directory for this entity type.
        overwrite : bool, default=False
            Whether to overwrite existing files.

        Returns
        -------
        str
            Destination path returned by the store.
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
        """Upload local files to the entity's storage path.

        Parameters
        ----------
        source : SourcesOrListOfSources
            Local file or files to upload.
        keep_dir_structure : bool, default=False
            Whether to preserve the source directory structure.

        Raises
        ------
        EntityErrorFileNotFound
            If a source file does not exist.
        EntityError
            If the upload fails for another supported storage or filesystem
            error.
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

    @property
    def files(self) -> list[dict]:
        """Return metadata for files associated with the entity.

        Returns
        -------
        list[dict]
            File metadata from the files API or the entity status.
        """
        if self._has_files_info():
            files_info = self._get_files_info()
            if files_info:
                return files_info
            if self.status.files:
                return self.status.files
        return []

    def _has_files_info(self) -> bool:
        return self.status.files is not None

    def _update_files_info(self, files_info: list[dict] | None = None) -> None:
        if files_info is None:
            return
        if len(files_info) <= MAX_FILES_IN_STATUS:
            self.status.files = files_info
            return
        self._log_files_info(files_info)

    def _log_files_info(self, files_info: list[dict]) -> None:
        if not files_info:
            return

        self.status.files = []
        self.save(update=True)
        material_processor.update_files_info(
            self.project,
            self.ENTITY_TYPE,
            self.id,
            files_info,
        )

    def _get_files_info(self) -> list[dict]:
        try:
            return material_processor.read_files_info(
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
