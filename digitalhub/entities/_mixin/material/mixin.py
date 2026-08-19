# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path
from typing import ClassVar

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities._processors.processors import material_processor
from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import BackendError
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities._mixin.material.status import MaterialStatus

logger = get_logger(__name__)


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
        self._obj_attr.extend(["extensions"])

    @refresh_decorator
    def as_file(self) -> list[str]:
        store = get_store(self.spec.path)
        dst = store._build_temp()
        return store.download(self.spec.path, dst=dst)

    @refresh_decorator
    def download(
        self,
        destination: str | None = None,
        overwrite: bool = False,
    ) -> str:
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
        store = get_store(self.spec.path)
        paths = store.upload(
            source,
            self.spec.path,
            keep_dir_structure=keep_dir_structure,
        )

        files_info = store.get_file_info(self.spec.path, paths)
        self._update_files_info(files_info)

    @property
    def files(self) -> list[dict]:
        if self._has_files_info():
            files_info = self._get_files_info()
            if files_info:
                return files_info
            if self.status.files:
                return self.status.files
        return []

    def _has_files_info(self) -> bool:
        return self.status.files is not None

    def get_file_paths(self) -> list[str]:
        return [f.get("path") for f in self.files]

    def _update_files_info(self, files_info: list[dict] | None = None) -> None:
        if files_info is None:
            return
        self._log_files_info(files_info)

    def _log_files_info(self, files_info: list[dict]) -> None:
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
        material_processor.update_files_info(
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
