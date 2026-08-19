# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import Callable

from digitalhub.entities._commons.enums import State
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiCategories, BackendOperations
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.exceptions import BuilderError, EntityError, EntityErrorFileNotFound, StoreError

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._base.material.protocol import MaterialEntityProtocol
    from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
    from digitalhub.entities.dataitem.table.entity import DataitemTable
    from digitalhub.utils.types import Dataframe, SourcesOrListOfSources


class ContextEntityMaterialProcessor:
    """
    Processor for material entity operations.

    Handles creation and management of material entities (artifacts,
    dataitems, models) including file upload operations and status
    management during uploads.
    """

    def __init__(self, crud_processor: ContextEntityCRUDProcessor):
        self.crud_processor = crud_processor

    def log_material_entity(
        self,
        **kwargs,
    ) -> MaterialEntityProtocol:
        """
        Create a material entity in the backend and upload associated files.

        Creates a new material entity (artifact, dataitem, or model) and
        handles file upload operations. Manages upload state transitions
        and error handling during the upload process.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        **kwargs : dict
            Parameters for entity creation including:
            - 'source': file source(s) to upload
            - 'project': project name
            - 'drop_existing': whether to drop existing entity with the same name

        Returns
        -------
        MaterialEntityProtocol
            The created material entity with uploaded files.
        """
        source: SourcesOrListOfSources = kwargs.pop("source")
        keep_dir_structure = kwargs.get("keep_dir_structure", False)
        return self._log_entity_with_upload(
            **kwargs,
            upload_fn=lambda obj: obj.upload(source, keep_dir_structure=keep_dir_structure),
        )

    def log_dataitem_table(
        self,
        **kwargs,
    ) -> DataitemTable:
        """
        Create a table dataitem entity in the backend and upload associated files.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        **kwargs : dict
            Parameters for entity creation including:
            - 'data': dataframe to upload
            - 'project': project name
            - 'drop_existing': whether to drop existing entity with the same name

        Returns
        -------
        DataitemTable
            The created table dataitem entity with uploaded files.
        """
        data: Dataframe = kwargs.pop("data")  # type: ignore
        return self._log_entity_with_upload(
            **kwargs,
            upload_fn=lambda obj: obj.write_df(data, extension=FileExtensions.PARQUET.value),
        )

    def log_dataitem_sql(
        self,
        **kwargs,
    ) -> DataitemTable:
        """
        Create a table dataitem entity in the backend with reference to
        a SQL table.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        **kwargs : dict
            Parameters for entity creation including:
            - 'project': project name
            - 'drop_existing': whether to drop existing entity with the same name

        Returns
        -------
        DataitemTable
            The created table dataitem entity.
        """
        return self._create_material_entity(**kwargs)

    def read_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        **kwargs,
    ) -> list[dict]:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.FILES.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.list_objects(api, **kwargs)

    def update_files_info(
        self,
        project: str,
        entity_type: str,
        entity_id: str,
        entity_list: list[dict],
        **kwargs,
    ) -> None:
        context = get_context(project)
        api = context.client.build_api(
            ApiCategories.CONTEXT.value,
            BackendOperations.FILES.value,
            project=context.name,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return context.client.update_object(api, entity_list, **kwargs)

    def _log_entity_with_upload(
        self,
        upload_fn: typing.Callable[[MaterialEntityProtocol], None],
        **kwargs,
    ) -> MaterialEntityProtocol:
        """
        Create an entity in the backend and execute upload operation.

        Common logic for creating material entities with file upload,
        handling status transitions and error management.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        upload_fn : Callable[[MaterialEntityProtocol], None]
            Function to execute for uploading data to the entity.
        **kwargs : dict
            Parameters for entity creation.

        Returns
        -------
        MaterialEntityProtocol
            The created material entity with uploaded files.
        """
        # Create entity in backend
        new_obj: MaterialEntityProtocol = self._create_material_entity(**kwargs)

        # Upload data to entity and manage status transitions
        return self._upload_material_entity(new_obj, upload_fn)

    def _create_material_entity(
        self,
        **kwargs,
    ) -> MaterialEntityProtocol:
        """
        Create a draft entity in the backend without file upload.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        **kwargs : dict
            Parameters for entity creation.

        Returns
        -------
        MaterialEntityProtocol
            The created draft material entity.
        """
        # Validate entity type
        drop_existing = kwargs.pop("drop_existing", False)
        kwargs = self._validate_entity_type(kwargs)

        # Build initial entity object
        obj: MaterialEntityProtocol = entity_factory.build_entity_from_params(**kwargs)

        # Register entity in context if running
        context = get_context(kwargs["project"])
        obj: MaterialEntityProtocol = self._register_entity_in_context(obj, context)

        # Handle existing entity drop
        self._drop_existing_entity(drop_existing, obj)

        # Create entity in backend and return
        new_obj: MaterialEntityProtocol = self.crud_processor._create_context_entity(
            context, obj.ENTITY_TYPE, obj.to_dict()
        )
        return entity_factory.build_entity_from_dict(new_obj)

    def _validate_entity_type(
        self,
        kwargs: dict,
    ) -> dict:
        """
        Validate that the entity type matches the expected type for the given kind.

        Parameters
        ----------
        kwargs : dict
            Parameters for entity creation including 'kind' and 'entity_type'.

        Returns
        -------
        dict
            The input parameters after validation.
        """
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
        obj: MaterialEntityProtocol,
        context: Context,
    ) -> MaterialEntityProtocol:
        """
        Register an entity in the context if it is running.

        Parameters
        ----------
        context : Context
            The execution context to register the entity in.
        obj : MaterialEntityProtocol
            The material entity object to register.

        Returns
        -------
        MaterialEntityProtocol
            The registered material entity.
        """
        if context.is_running:
            obj = context.register_entity(obj)
        return obj

    def _drop_existing_entity(
        self,
        drop_existing: bool,
        obj: MaterialEntityProtocol,
    ) -> None:
        """
        Drop an existing entity with the same name if it exists.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        drop_existing : bool
            Flag indicating whether to drop the existing entity if it exists.
        obj : MaterialEntityProtocol
            The material entity object to drop.
        """
        if drop_existing:
            self.crud_processor.delete_context_entity(
                obj.name,
                project=obj.project,
                entity_type=obj.ENTITY_TYPE,
                delete_all_versions=True,
            )

    def _upload_material_entity(
        self,
        obj: MaterialEntityProtocol,
        upload_fn: Callable,
    ) -> MaterialEntityProtocol:
        """
        Upload data to a material entity.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        obj : MaterialEntityProtocol
            The material entity to upload data to.
        upload_fn : Callable[[MaterialEntityProtocol], None]
            Function to execute for uploading data to the entity.

        Returns
        -------
        MaterialEntityProtocol
            The material entity after upload.
        """
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
        new_obj: MaterialEntityProtocol,
    ) -> MaterialEntityProtocol:
        """
        Update a material entity using a shortcut method.

        Convenience method for updating material entities during
        file upload operations.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        new_obj : MaterialEntityProtocol
            The material entity object to update.

        Returns
        -------
        MaterialEntityProtocol
            The updated material entity.
        """
        return self.crud_processor.update_context_entity(
            new_obj.project,
            new_obj.ENTITY_TYPE,
            new_obj.id,
            new_obj.to_dict(),
        )
