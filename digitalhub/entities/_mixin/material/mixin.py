# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import ClassVar

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities._mixin.extensions.mixin import ExtensionsMixin
from digitalhub.entities._mixin.material.files import MaterialFile
from digitalhub.entities._processors.processors import material_processor
from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities._mixin.material.status import MaterialStatus

logger = get_logger(__name__)
MAX_FILES_IN_STATUS = 100


class MaterialMixin(ExtensionsMixin):
    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str
    spec: MaterialSpec
    status: MaterialStatus

    @refresh_decorator
    @contextmanager
    def as_file(self) -> Generator[list[str], None, None]:
        """Temporarily download the entity's files.

        Returns
        -------
        Generator[list[str], None, None]
            Context manager yielding paths to downloaded files.
        """
        store = get_store(self.spec.path)
        with TemporaryDirectory() as temp_dir:
            yield store.download(self.spec.path, dst=Path(temp_dir))

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
        material_processor.upload_material(
            self,
            source,
            keep_dir_structure=keep_dir_structure,
        )

    @property
    def files(self) -> list[MaterialFile]:
        """Return file objects associated with the entity.

        Returns
        -------
        list[MaterialFile]
            Objects built from the files API or the entity status.
        """
        if not self._has_files_info():
            return []

        files_info = self._get_files_info()
        if not files_info:
            files_info = self.status.files or []
        if not files_info:
            return []

        context_root = self._context().root / self.ENTITY_TYPE
        material_files = []
        for file_info in files_info:
            file_info = file_info or {}
            material_files.append(
                MaterialFile(
                    path=file_info.get("path"),
                    name=file_info.get("name"),
                    content_type=file_info.get("content_type"),
                    size=file_info.get("size"),
                    hash=file_info.get("hash"),
                    last_modified=file_info.get("last_modified"),
                    material_path=self.spec.path,
                    context_root=context_root,
                )
            )
        return material_files

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
        self.update()
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
