# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Generator
from contextlib import contextmanager
from typing import ClassVar

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities._mixin.extensions.mixin import ExtensionsMixin
from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor
from digitalhub.utils.types import SourcesOrListOfSources

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.files import MaterialFile
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities._mixin.material.status import MaterialStatus


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
        with ContextEntityMaterialProcessor().as_file(self) as files:
            yield files

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
        return ContextEntityMaterialProcessor().download_material(
            self,
            destination=destination,
            overwrite=overwrite,
        )

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
        ContextEntityMaterialProcessor().upload_material(
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
        return ContextEntityMaterialProcessor().get_material_files(self)
