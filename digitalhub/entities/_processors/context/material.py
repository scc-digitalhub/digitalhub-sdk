# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from digitalhub.context.api import get_default_store
from digitalhub.entities._commons.enums import State
from digitalhub.entities._commons.utils import build_log_path_from_source
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._mixin.material.files import MaterialFile
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.stores.data.api import get_store
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.exceptions import BackendError, BuilderError, EntityError, EntityErrorFileNotFound
from digitalhub.utils.logger.logger import get_logger

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.protocol import MaterialProtocol
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
    from digitalhub.entities.dataitem.table.entity import DataitemTable
    from digitalhub.utils.types import Dataframe, SourcesOrListOfSources

logger = get_logger(__name__)
MAX_FILES_IN_STATUS = 100


class ContextEntityMaterialProcessor:
    def __init__(self, crud_processor: ContextEntityCRUDProcessor):
        self.crud_processor = crud_processor

    def build_log_kwargs(
        self,
        project: str,
        name: str,
        entity_type: str,
        source: SourcesOrListOfSources,
        path: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build storage parameters for a material log operation."""
        if path is None:
            default_store = get_default_store(project)
            uuid = build_uuid()
            kwargs["uuid"] = uuid
            kwargs["path"] = build_log_path_from_source(
                project,
                entity_type,
                name,
                uuid,
                source,
                default_store=default_store,
            )
        else:
            kwargs["path"] = path
        return kwargs

    def log_material_entity(self, **kwargs) -> MaterialProtocol:
        source: SourcesOrListOfSources = kwargs.pop("source")
        keep_dir_structure = kwargs.pop("keep_dir_structure", False)
        return self._log_entity_with_upload(
            **kwargs,
            upload_fn=lambda obj: self._upload_material_files(
                obj,
                source,
                keep_dir_structure,
            ),
        )

    def log_dataitem_table(self, **kwargs) -> DataitemTable:
        data: Dataframe = kwargs.pop("data")  # type: ignore
        return self._log_entity_with_upload(
            **kwargs,
            upload_fn=lambda obj: obj.write_df(data, extension=FileExtensions.PARQUET.value),
        )

    def log_dataitem_sql(self, **kwargs) -> DataitemTable:
        return self._create_material_entity(**kwargs)

    def upload_material(
        self,
        obj: MaterialProtocol,
        source: SourcesOrListOfSources,
        keep_dir_structure: bool = False,
    ) -> MaterialProtocol:
        return self._upload_material_entity(
            obj,
            lambda entity: self._upload_material_files(
                entity,
                source,
                keep_dir_structure,
            ),
        )

    @contextmanager
    def as_file(self, obj: MaterialProtocol) -> Generator[list[str], None, None]:
        """Temporarily download an entity's material into a local directory."""
        store = get_store(obj.spec.path)
        with TemporaryDirectory() as temp_dir:
            yield store.download(obj.spec.path, dst=Path(temp_dir))

    def download_material(
        self,
        obj: MaterialProtocol,
        destination: str | None = None,
        overwrite: bool = False,
    ) -> str:
        """Download an entity's material to an explicit or project-local path."""
        if destination is None:
            destination_path = get_context(obj.project).root / obj.ENTITY_TYPE
        else:
            destination_path = Path(destination)
        return get_store(obj.spec.path).download(obj.spec.path, destination_path, overwrite=overwrite)

    def get_material_files(self, obj: MaterialProtocol) -> list[MaterialFile]:
        """Build file objects from backend metadata, falling back to entity status."""
        if obj.status.files is None:
            return []

        try:
            files_info = self.read_files_info(
                project=obj.project,
                entity_type=obj.ENTITY_TYPE,
                entity_id=obj.id,
            )
        except BackendError:
            logger.debug(
                f"Could not retrieve files info for entity '{obj.id}' from backend.",
                exc_info=True,
            )
            files_info = []

        if not files_info:
            files_info = obj.status.files or []
        if not files_info:
            return []

        context_root = get_context(obj.project).root / obj.ENTITY_TYPE
        return [
            MaterialFile(
                path=file_info.get("path"),
                name=file_info.get("name"),
                content_type=file_info.get("content_type"),
                size=file_info.get("size"),
                hash=file_info.get("hash"),
                last_modified=file_info.get("last_modified"),
                material_path=obj.spec.path,
                context_root=context_root,
            )
            for file_info in (info or {} for info in files_info)
        ]

    def update_material_files(
        self,
        obj: MaterialProtocol,
        files_info: list[dict] | None = None,
    ) -> None:
        """Store small file lists on the entity and large lists through the files API."""
        if files_info is None:
            return
        if len(files_info) <= MAX_FILES_IN_STATUS:
            obj.status.files = files_info
            return

        obj.status.files = []
        obj.update()
        self.update_files_info(
            obj.project,
            obj.ENTITY_TYPE,
            obj.id,
            files_info,
        )

    def read_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
    ) -> list[dict]:
        """Read information about files associated with a specific entity."""
        context = get_context(project)
        return context.client.execute_list(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.FILES_READ,
                target=ContextEntityTarget(context.name, entity_type, entity_id),
            )
        )

    def update_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_list: list[dict],
    ) -> None:
        """Update information about files associated with a specific entity."""
        context = get_context(project)
        context.client.execute(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.FILES_UPDATE,
                target=ContextEntityTarget(context.name, entity_type, entity_id),
                payload=entity_list,
            )
        )

    def _log_entity_with_upload(
        self,
        upload_fn: typing.Callable[[MaterialProtocol], object],
        **kwargs,
    ) -> MaterialProtocol:
        new_obj: MaterialProtocol = self._create_material_entity(**kwargs)
        return self._upload_material_entity(new_obj, upload_fn)

    def _create_material_entity(
        self,
        **kwargs,
    ) -> MaterialProtocol:
        drop_existing = kwargs.pop("drop_existing", False)
        entity_kind = kwargs["kind"]
        entity_type = kwargs.pop("entity_type")
        try:
            expected_type = entity_factory.get_entity_type_from_kind(entity_kind)
        except BuilderError:
            expected_type = entity_type
        if entity_type != expected_type:
            raise ValueError(
                f"Entity kind '{entity_kind}' does not match expected type '{expected_type}'.",
            )
        obj: MaterialProtocol = entity_factory.build_entity_from_params(**kwargs)
        context = get_context(obj.project)
        if context.is_running:
            obj = context.register_entity(obj)

        if drop_existing:
            self.crud_processor.delete_context_entity(
                obj.name,
                project=obj.project,
                entity_type=obj.ENTITY_TYPE,
                delete_all_versions=True,
            )
        backend_obj = self.crud_processor._create_context_entity(
            context,
            obj.ENTITY_TYPE,
            obj.to_dict(),
        )
        return entity_factory.build_entity_from_dict(backend_obj, entity_type=obj.ENTITY_TYPE)

    def _upload_material_entity(
        self,
        obj: MaterialProtocol,
        upload_fn: Callable[[MaterialProtocol], object],
    ) -> MaterialProtocol:
        try:
            obj.status.state = State.UPLOADING.value
            obj = self._update_material_entity(obj)
            upload_fn(obj)
            obj.status.message = None
            obj.status.state = State.READY.value
            return self._update_material_entity(obj)
        except Exception as error:
            if isinstance(error, (FileNotFoundError, EntityErrorFileNotFound)):
                msg = f"Upload failed: {error}. Please verify that the specified source files are correct and exist."
                error_type = EntityErrorFileNotFound
            else:
                msg = f"Upload failed: {error}"
                error_type = EntityError

            obj.status.message = msg
            obj.status.state = State.ERROR.value
            try:
                self._update_material_entity(obj)
            except Exception as status_error:
                msg = f"{msg}; failed to persist ERROR status: {status_error}"
                obj.status.message = msg
                raise error_type(msg) from status_error

            raise error_type(msg) from error

    def _upload_material_files(
        self,
        obj: MaterialProtocol,
        source: SourcesOrListOfSources,
        keep_dir_structure: bool,
    ) -> None:
        store = get_store(obj.spec.path)
        paths = store.upload(
            source,
            obj.spec.path,
            keep_dir_structure=keep_dir_structure,
        )
        files_info = store.get_file_info(obj.spec.path, paths)
        self.update_material_files(obj, files_info)

    def _update_material_entity(
        self,
        new_obj: MaterialProtocol,
    ) -> MaterialProtocol:
        updated_obj = self.crud_processor.update_context_entity(
            new_obj.project,
            new_obj.ENTITY_TYPE,
            new_obj.id,
            new_obj.to_dict(),
        )
        new_obj._update_attributes(updated_obj)
        return new_obj
