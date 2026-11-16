# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from typing_extensions import Self

from digitalhub.entities._commons.utils import build_zip_path
from digitalhub.entities._mixin.source.models import SourceCode
from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol
from digitalhub.stores.data.api import get_store
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.file_utils import eval_zip_type
from digitalhub.utils.generic_utils import create_archive, decode_base64_string, read_source
from digitalhub.utils.io_utils import write_text
from digitalhub.utils.uri_utils import has_local_scheme

if TYPE_CHECKING:
    from digitalhub.context.context import Context


class _SourceSpec(Protocol):
    source: SourceCode | None


class _SourceEntity(Protocol):
    spec: _SourceSpec
    project: str
    name: str
    id: str
    ENTITY_TYPE: str

    def _context(self) -> Context: ...


class _ExportBase(Protocol):
    def export(self) -> str: ...


class SourceEntityMixin:
    """Handle source file uploads and local source export for versioned entities."""

    def _is_inlineable_source(self, path: str) -> bool:
        raise NotImplementedError(f"{type(self).__name__} must define inlineable source types for {path!r}.")

    def _read_inline_source(self, path: str) -> str:
        return read_source(path)

    def _post_build_source_check(self) -> Self:
        entity = cast(_SourceEntity, self)
        source = entity.spec.source
        if source is None or source.source is None or source.base64 is not None:
            return self

        source_path = source.source
        if not source_path or not has_local_scheme(source_path):
            return self

        path = Path(source_path)
        if not path.exists():
            raise EntityError(f"Source {source_path} does not exist.")

        if path.is_dir():
            with create_archive(path) as archive_path:
                destination = build_zip_path(cast(VersionedEntityProtocol, entity), archive_path.name)
                get_store(destination).upload(str(archive_path), destination)
            source.source = destination
        elif eval_zip_type(source_path):
            destination = build_zip_path(cast(VersionedEntityProtocol, entity), path.name)
            get_store(destination).upload(source_path, destination)
            source.source = destination
        elif self._is_inlineable_source(source_path):
            source.base64 = self._read_inline_source(source_path)

        return self

    def export(self) -> str:
        entity = cast(_SourceEntity, self)
        source = entity.spec.source
        if source is None or source.source is None or source.base64 is None or not has_local_scheme(source.source):
            return cast(_ExportBase, super()).export()

        source_path = source.source
        base64 = source.base64
        source.base64 = None
        try:
            write_text(entity._context().root / source_path, decode_base64_string(base64))
            return cast(_ExportBase, super()).export()
        finally:
            source.base64 = base64
