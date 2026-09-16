# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Callable

from digitalhub.entities._commons.enums import State
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.exceptions import BuilderError, EntityError, EntityErrorFileNotFound, StoreError

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._mixin.material.protocol import MaterialProtocol
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
    from digitalhub.entities.dataitem.table.entity import DataitemTable
    from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


class ContextEntityMaterialProcessor:
    def __init__(self, crud_processor: ContextEntityCRUDProcessor):
        self.crud_processor = crud_processor

    def log_material_entity(self, **kwargs) -> MaterialProtocol:
        source: SourcesOrListOfSources = kwargs.pop("source")
        keep_dir_structure = kwargs.get("keep_dir_structure", False)
        return self._log_entity_with_upload(
            **kwargs,
            upload_fn=lambda obj: obj.upload(source, keep_dir_structure=keep_dir_structure),
        )

    def log_dataitem_table(self, **kwargs) -> DataitemTable:
        data: Dataframe = kwargs.pop("data")  # type: ignore
        return self._log_entity_with_upload(
            **kwargs,
            upload_fn=lambda obj: obj.write_df(data, extension=FileExtensions.PARQUET.value),
        )

    def log_dataitem_sql(self, **kwargs) -> DataitemTable:
        return self._create_material_entity(**kwargs)

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
        upload_fn: typing.Callable[[MaterialProtocol], None],
        **kwargs,
    ) -> MaterialProtocol:
        new_obj: MaterialProtocol = self._create_material_entity(**kwargs)
        return self._upload_material_entity(new_obj, upload_fn)

    def _create_material_entity(
        self,
        **kwargs,
    ) -> MaterialProtocol:
        # Validate entity type
        drop_existing = kwargs.pop("drop_existing", False)
        kwargs = self._validate_entity_type(kwargs)

        # Build initial entity object
        obj: MaterialProtocol = entity_factory.build_entity_from_params(**kwargs)

        # Register entity in context if running
        context = get_context(kwargs["project"])
        obj: MaterialProtocol = self._register_entity_in_context(obj, context)

        # Handle existing entity drop
        self._drop_existing_entity(drop_existing, obj)

        # Create entity in backend and return
        new_obj: MaterialProtocol = self.crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        return entity_factory.build_entity_from_dict(new_obj, entity_type=obj.ENTITY_TYPE)

    def _validate_entity_type(self, kwargs: dict) -> dict:
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
        return kwargs

    def _register_entity_in_context(
        self,
        obj: MaterialProtocol,
        context: Context,
    ) -> MaterialProtocol:
        if context.is_running:
            obj = context.register_entity(obj)
        return obj

    def _drop_existing_entity(
        self,
        drop_existing: bool,
        obj: MaterialProtocol,
    ) -> None:
        if drop_existing:
            self.crud_processor.delete_context_entity(
                obj.name,
                project=obj.project,
                entity_type=obj.ENTITY_TYPE,
                delete_all_versions=True,
            )

    def _upload_material_entity(
        self,
        obj: MaterialProtocol,
        upload_fn: Callable,
    ) -> MaterialProtocol:
        # Update status to UPLOADING before upload
        obj.status.state = State.UPLOADING.value
        obj = self._update_material_entity(obj)

        # Handle file upload
        error: Exception | None = None
        try:
            upload_fn(obj)
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

        obj.status.message = msg

        # Update status after upload
        if uploaded:
            obj.status.state = State.READY.value
            obj = self._update_material_entity(obj)
        else:
            obj.status.state = State.ERROR.value
            obj = self._update_material_entity(obj)
            raise exception(msg) from error

        return obj

    def _update_material_entity(
        self,
        new_obj: MaterialProtocol,
    ) -> MaterialProtocol:
        return self.crud_processor.update_context_entity(
            new_obj.project,
            new_obj.ENTITY_TYPE,
            new_obj.id,
            new_obj.to_dict(),
        )
