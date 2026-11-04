# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import EntityError


class MaterialFile:
    """File metadata with download operations for one material file."""

    def __init__(
        self,
        path: str | None,
        name: str | None,
        content_type: str | None,
        size: int | None,
        hash: str | None,
        last_modified: str | None,
        material_path: str,
        context_root: Path,
    ) -> None:
        self._material_path = material_path
        self._context_root = context_root
        self.path = path
        self.name = name
        self.content_type = content_type
        self.size = size
        self.hash = hash
        self.last_modified = last_modified

    def __repr__(self) -> str:
        fields = {
            "path": self.path,
            "name": self.name,
            "content_type": self.content_type,
            "size": self.size,
            "hash": self.hash,
            "last_modified": self.last_modified,
        }
        return str({key: value for key, value in fields.items() if value is not None})

    def as_file(self) -> str:
        """Download this file into a temporary directory.

        Returns
        -------
        str
            Path to the downloaded file.
        """
        store = get_store(self._material_path)
        dst = store._build_temp()
        return store.download(self._get_download_path(), dst=dst)

    def download(
        self,
        destination: str | None = None,
        overwrite: bool = False,
    ) -> str:
        """Download this file to a local destination.

        Parameters
        ----------
        destination : str, optional
            Local destination directory. If omitted, use the project context
            directory for this entity type.
        overwrite : bool, default=False
            Whether to overwrite an existing file.

        Returns
        -------
        str
            Destination path returned by the store.
        """
        store = get_store(self._material_path)

        if destination is None:
            dst = self._context_root
        else:
            dst = Path(destination)

        return store.download(self._get_download_path(), dst, overwrite=overwrite)

    def _get_download_path(self) -> str:
        if not self._material_path.endswith("/"):
            return self._material_path
        if not self.path:
            raise EntityError("Cannot download a file from a material partition without a file path.")
        return f"{self._material_path}{self.path.lstrip('/')}"
