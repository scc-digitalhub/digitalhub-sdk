# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import State
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.enums import FileExtensions
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.material.entity import MaterialEntity
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

    def log_material_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        **kwargs,
    ) -> MaterialEntity:
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
        MaterialEntity
            The created material entity with uploaded files.

        Raises
        ------
        EntityError
            If file upload fails during the process.
        """
        source: SourcesOrListOfSources = kwargs.pop("source")
        return self._log_entity_with_upload(
            crud_processor,
            upload_fn=lambda obj: obj.upload(source),
            **kwargs,
        )

    def log_dataitem_table(
        self,
        crud_processor: ContextEntityCRUDProcessor,
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
        data: Dataframe = kwargs.pop("data")
        return self._log_entity_with_upload(
            crud_processor,
            upload_fn=lambda obj: obj.write_df(data, extension=FileExtensions.PARQUET.value),
            **kwargs,
        )

    def _log_entity_with_upload(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        upload_fn: typing.Callable[[MaterialEntity], None],
        **kwargs,
    ) -> MaterialEntity:
        """
        Create an entity in the backend and execute upload operation.

        Common logic for creating material entities with file upload,
        handling status transitions and error management.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        upload_fn : Callable[[MaterialEntity], None]
            Function to execute for uploading data to the entity.
        **kwargs : dict
            Parameters for entity creation.

        Returns
        -------
        MaterialEntity
            The created material entity with uploaded files.

        Raises
        ------
        EntityError
            If file upload fails during the process.
        """
        entity_kind = kwargs.get("kind")

        # Validate entity type
        entity_type = kwargs.pop("entity_type")
        if entity_type != entity_factory.get_entity_type_from_kind(entity_kind):
            raise ValueError(
                f"Entity kind '{entity_kind}' does not match expected type '{entity_type}'.",
            )

        # Build initial entity object
        obj: MaterialEntity = entity_factory.build_entity_from_params(**kwargs)

        # Register entity in context if running
        context = get_context(kwargs["project"])
        if context.is_running:
            obj = context.register_entity(obj)

        # Handle existing entity drop
        drop_existing: bool = kwargs.pop("drop_existing", False)
        if drop_existing:
            crud_processor.delete_context_entity(
                kwargs["name"],
                project=kwargs["project"],
                entity_type=obj.ENTITY_TYPE,
                delete_all_versions=True,
            )

        # Create entity in backend
        new_obj: MaterialEntity = crud_processor._create_context_entity(context, obj.ENTITY_TYPE, obj.to_dict())
        new_obj = entity_factory.build_entity_from_dict(new_obj)

        # Update status to UPLOADING before upload
        new_obj.status.state = State.UPLOADING.value
        new_obj = self._update_material_entity(crud_processor, new_obj)

        # Handle file upload
        try:
            upload_fn(new_obj)
            uploaded = True
            msg = None
        except Exception as e:
            uploaded = False
            msg = str(e.args)

        new_obj.status.message = msg

        # Update status after upload
        if uploaded:
            new_obj.status.state = State.READY.value
            new_obj = self._update_material_entity(crud_processor, new_obj)
        else:
            new_obj.status.state = State.ERROR.value
            new_obj = self._update_material_entity(crud_processor, new_obj)
            raise EntityError(msg)

        return new_obj

    def _update_material_entity(
        self,
        crud_processor: ContextEntityCRUDProcessor,
        new_obj: MaterialEntity,
    ) -> MaterialEntity:
        """
        Update a material entity using a shortcut method.

        Convenience method for updating material entities during
        file upload operations.

        Parameters
        ----------
        crud_processor : ContextEntityCRUDProcessor
            The CRUD processor instance for entity operations.
        new_obj : MaterialEntity
            The material entity object to update.

        Returns
        -------
        MaterialEntity
            The updated material entity.
        """
        return crud_processor.update_context_entity(
            new_obj.project,
            new_obj.ENTITY_TYPE,
            new_obj.id,
            new_obj.to_dict(),
        )
