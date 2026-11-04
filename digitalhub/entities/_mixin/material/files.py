# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import posixpath
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

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

    def as_file(self) -> str:
        """Download this file into a temporary directory.

        Returns
        -------
        str
            Path to the downloaded file.
        """
        store = get_store(self._material_path)
        dst = store._build_temp()
        return store.download(self._get_storage_path(), dst=dst)

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

        return store.download(self._get_storage_path(), dst, overwrite=overwrite)

    def _get_storage_path(self) -> str:
        if not self.path:
            raise EntityError("Cannot download a material file without a storage path.")

        if urlsplit(self.path).scheme:
            return self.path

        root = urlsplit(self._material_path)
        path = posixpath.join(root.path.rstrip("/"), self.path.lstrip("/"))
        if not path.startswith("/"):
            path = f"/{path}"
        return urlunsplit(root._replace(path=path))
