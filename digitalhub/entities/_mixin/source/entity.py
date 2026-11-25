# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast

from typing_extensions import Self

from digitalhub.entities._commons.utils import build_zip_path
from digitalhub.entities._mixin.source.protocol import SourceEntityProtocol
from digitalhub.stores.data.api import get_default_store_uri, get_store
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.file_utils import eval_zip_type
from digitalhub.utils.generic_utils import create_archive, decode_base64_string, read_source
from digitalhub.utils.io_utils import write_text
from digitalhub.utils.uri_utils import has_local_scheme


class _ExportBase(Protocol):
    def export(self) -> str: ...


class SourceEntityMixin:
    """Handle source file uploads and local source export for versioned entities."""

    @property
    def source(self) -> str | None:
        source = cast(SourceEntityProtocol, self).spec.source
        if source is None:
            return None
        if source.base64 is not None:
            return decode_base64_string(source.base64)
        return source.code

    def _is_inlineable_source(self, path: str) -> bool:
        raise NotImplementedError(f"{type(self).__name__} must define inlineable source types for {path!r}.")

    def _read_inline_source(self, path: str) -> str:
        return read_source(path)

    @staticmethod
    def _resolve_export_path(root: Path, source_path: str) -> Path:
        relative_path = Path(source_path)
        if relative_path.is_absolute():
            raise EntityError(f"Source path {source_path!r} is outside the context root.")

        resolved_root = root.resolve()
        destination = (resolved_root / relative_path).resolve()
        if not destination.is_relative_to(resolved_root):
            raise EntityError(f"Source path {source_path!r} is outside the context root.")
        return destination

    def _post_build_source_check(self) -> Self:
        entity = cast(SourceEntityProtocol, self)
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
                destination = build_zip_path(
                    entity,
                    archive_path.name,
                    default_store=get_default_store_uri(entity._context().config),
                )
                get_store(destination, entity.project).upload(str(archive_path), destination)
            source.source = destination
        elif eval_zip_type(source_path):
            destination = build_zip_path(
                entity,
                path.name,
                default_store=get_default_store_uri(entity._context().config),
            )
            get_store(destination, entity.project).upload(source_path, destination)
            source.source = destination
        elif self._is_inlineable_source(source_path):
            source.base64 = self._read_inline_source(source_path)

        return self

    def export(self) -> str:
        entity = cast(SourceEntityProtocol, self)
        source = entity.spec.source
        if source is None or source.source is None or source.base64 is None or not has_local_scheme(source.source):
            return cast(_ExportBase, super()).export()

        source_path = source.source
        base64 = source.base64
        context = entity._context()
        destination = self._resolve_export_path(context.ensure_root(), source_path)
        content = decode_base64_string(base64)
        source.base64 = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            write_text(destination, content)
            return cast(_ExportBase, super()).export()
        finally:
            source.base64 = base64
