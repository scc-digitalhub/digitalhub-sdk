# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from functools import wraps
from pathlib import Path
from typing import Any

from digitalhub.context.api import build_context
from digitalhub.entities._base.entity.entity import Entity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.processors import base_processor, context_processor
from digitalhub.entities.project._base.crud_manager import CRUDManager
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.base.factory import get_client
from digitalhub.utils.exceptions import BackendError, EntityAlreadyExistsError, EntityError
from digitalhub.utils.io_utils import write_yaml
from digitalhub.utils.uri_utils import has_local_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.artifact._base.entity import Artifact
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.entities.function._base.entity import Function
    from digitalhub.entities.model._base.entity import Model
    from digitalhub.entities.project._base.spec import ProjectSpec
    from digitalhub.entities.project._base.status import ProjectStatus
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.secret._base.entity import Secret
    from digitalhub.entities.workflow._base.entity import Workflow


def _auto_refresh(method):
    """Decorator to automatically refresh project after method execution."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        self.refresh()
        return result

    return wrapper


class Project(Entity):
    """
    A class representing a project.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value

    def __init__(
        self,
        name: str,
        kind: str,
        metadata: Metadata,
        spec: ProjectSpec,
        status: ProjectStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.spec: ProjectSpec
        self.status: ProjectStatus

        self.id = name
        self.name = name
        self.key = base_processor.build_project_key(self.name)

        self._obj_attr.extend(["id", "name"])

        # Set client
        self._client = get_client()

        # Set context
        build_context(self)

        # Set CRUD manager
        self.crud = CRUDManager(self.name)

    ##############################
    #  Save / Refresh / Export
    ##############################

    def save(self, update: bool = False) -> Project:
        """
        Save entity into backend.

        Parameters
        ----------
        update : bool
            If True, the object will be updated.

        Returns
        -------
        Project
            Entity saved.
        """
        if update:
            new_obj = base_processor.update_project_entity(
                entity_type=self.ENTITY_TYPE,
                entity_name=self.name,
                entity_dict=self.to_dict(),
            )
        else:
            new_obj = base_processor.create_project_entity(_entity=self)
        self._update_attributes(new_obj)
        return self

    def refresh(self) -> Project:
        """
        Refresh object from backend.

        Returns
        -------
        Project
            Project object.
        """
        new_obj = base_processor.read_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
        )
        self._update_attributes(new_obj)
        return self

    def search_entity(
        self,
        query: str | None = None,
        entity_types: list[str] | None = None,
        name: str | None = None,
        kind: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> tuple[list[ContextEntity], list[dict]]:
        """
        Search objects from backend.

        See also
        --------
        digitalhub.search_entity
        """
        return context_processor.search_entity(
            self.name,
            query=query,
            entity_types=entity_types,
            name=name,
            kind=kind,
            created=created,
            updated=updated,
            description=description,
            labels=labels,
            **kwargs,
        )

    def export(self) -> str:
        """
        Export object as a YAML file in the context folder.
        If the objects are not embedded, the objects are exported as a YAML file.

        Returns
        -------
        str
            Exported filepath.
        """
        obj = self._refresh_to_dict()
        pth = Path(self.spec.source) / f"{self.ENTITY_TYPE}s-{self.name}.yaml"
        obj = self._export_not_embedded(obj)
        write_yaml(pth, obj)
        return str(pth)

    def _refresh_to_dict(self) -> dict:
        """
        Try to refresh object to collect entities related to project.

        Returns
        -------
        dict
            Entity object in dictionary format.
        """
        try:
            return self.refresh().to_dict()
        except BackendError:
            return self.to_dict()

    def _export_not_embedded(self, obj: dict) -> dict:
        """
        Export project objects if not embedded.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.

        Returns
        -------
        dict
            Updatated project object in dictionary format with referenced entities.
        """
        # Cycle over entity types
        for entity_type in self._get_entity_types():
            # Entity types are stored as a list of entities
            for idx, entity in enumerate(obj.get("spec", {}).get(entity_type, [])):
                # Export entity if not embedded is in metadata, else do nothing
                if not self._is_embedded(entity):
                    # Get entity object from backend
                    ent = context_processor.read_context_entity(entity["key"])

                    # Export and store ref in object metadata inside project
                    pth = ent.export()
                    obj["spec"][entity_type][idx]["metadata"]["ref"] = pth

        # Return updated object
        return obj

    def _import_entities(self, obj: dict, reset_id: bool = False) -> None:
        """
        Import project entities.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.
        """
        entity_types = self._get_entity_types()

        # Cycle over entity types
        for entity_type in entity_types:
            # Entity types are stored as a list of entities
            for entity in obj.get("spec", {}).get(entity_type, []):
                embedded = self._is_embedded(entity)
                ref = entity["metadata"].get("ref")

                # Import entity if not embedded and there is a ref
                if not embedded and ref is not None:
                    # Import entity from local ref
                    if has_local_scheme(ref):
                        try:
                            # Artifacts, Dataitems and Models
                            if entity_type in entity_types[:3]:
                                context_processor.import_context_entity(
                                    file=ref,
                                    reset_id=reset_id,
                                    context=self.name,
                                )

                            # Functions and Workflows
                            elif entity_type in entity_types[3:]:
                                context_processor.import_executable_entity(
                                    file=ref,
                                    reset_id=reset_id,
                                    context=self.name,
                                )

                        except FileNotFoundError:
                            msg = f"File not found: {ref}."
                            raise EntityError(msg)

                # If entity is embedded, create it and try to save
                elif embedded:
                    # It's possible that embedded field in metadata is not shown
                    if entity["metadata"].get("embedded") is None:
                        entity["metadata"]["embedded"] = True

                    if reset_id:
                        new_id = build_uuid()
                        entity["id"] = new_id
                        entity["metadata"]["version"] = new_id

                    try:
                        entity_factory.build_entity_from_dict(entity).save()
                    except EntityAlreadyExistsError:
                        pass

    def _load_entities(self, obj: dict) -> None:
        """
        Load project entities.

        Parameters
        ----------
        obj : dict
            Project object in dictionary format.
        """
        entity_types = self._get_entity_types()

        # Cycle over entity types
        for entity_type in entity_types:
            # Entity types are stored as a list of entities
            for entity in obj.get("spec", {}).get(entity_type, []):
                embedded = self._is_embedded(entity)
                ref = entity["metadata"].get("ref")

                # Load entity if not embedded and there is a ref
                if not embedded and ref is not None:
                    # Load entity from local ref
                    if has_local_scheme(ref):
                        try:
                            # Artifacts, Dataitems and Models
                            if entity_type in entity_types[:3]:
                                context_processor.load_context_entity(ref)

                            # Functions and Workflows
                            elif entity_type in entity_types[3:]:
                                context_processor.load_executable_entity(ref)

                        except FileNotFoundError:
                            msg = f"File not found: {ref}."
                            raise EntityError(msg)

    def _is_embedded(self, entity: dict) -> bool:
        """
        Check if entity is embedded.

        Parameters
        ----------
        entity : dict
            Entity in dictionary format.

        Returns
        -------
        bool
            True if entity is embedded.
        """
        metadata_embedded = entity["metadata"].get("embedded", False)
        no_status = entity.get("status", None) is None
        no_spec = entity.get("spec", None) is None
        return metadata_embedded or not (no_status and no_spec)

    def _get_entity_types(self) -> list[str]:
        """
        Get entity types.

        Returns
        -------
        list
            Entity types.
        """
        return [
            f"{EntityTypes.ARTIFACT.value}s",
            f"{EntityTypes.DATAITEM.value}s",
            f"{EntityTypes.MODEL.value}s",
            f"{EntityTypes.FUNCTION.value}s",
            f"{EntityTypes.WORKFLOW.value}s",
        ]

    def _validate_entity_project(self, project: str) -> None:
        """
        Validate that entity belongs to this project.

        Parameters
        ----------
        project : str
            Project name of the entity.
        """
        if project != self.name:
            raise ValueError(f"Entity to update is not in project {self.name}.")

    ##############################
    #  Artifacts
    ##############################

    @_auto_refresh
    def new_artifact(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create a new artifact.

        See also
        -------
        digitalhub.new_artifact
        """
        return self.crud.artifact.new(
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def log_artifact(
        self,
        name: str,
        kind: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create and upload an artifact.

        See also
        -------
        digitalhub.log_artifact
        """
        return self.crud.artifact.log(
            name=name,
            kind=kind,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def log_generic_artifact(
        self,
        name: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Artifact:
        """
        Create and upload a generic artifact.

        See also
        -------
        digitalhub.log_generic_artifact
        """
        return self.crud.artifact.log_generic(
            name=name,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def get_artifact(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Artifact:
        """
        Get artifact from backend.

        See also
        -------
        digitalhub.get_artifact
        """
        return self.crud.artifact.get(
            identifier=identifier,
            entity_id=entity_id,
        )

    @_auto_refresh
    def get_artifact_versions(
        self,
        identifier: str,
    ) -> list[Artifact]:
        """
        Get artifact versions from backend.

        See also
        -------
        digitalhub.get_artifact_versions
        """
        return self.crud.artifact.get_versions(identifier=identifier)

    @_auto_refresh
    def list_artifacts(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
    ) -> list[Artifact]:
        """
        List all latest version artifacts from backend.

        See also
        -------
        digitalhub.list_artifacts
        """
        return self.crud.artifact.list(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            versions=versions,
        )

    @_auto_refresh
    def import_artifact(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Artifact:
        """
        Import artifact into backend from a YAML file or key.

        See also
        -------
        digitalhub.import_artifact
        """
        return self.crud.artifact.import_entity(file=file, key=key, reset_id=reset_id)

    @_auto_refresh
    def update_artifact(
        self,
        entity: Artifact,
    ) -> Artifact:
        """
        Update artifact.

        See also
        -------
        digitalhub.update_artifact
        """
        self._validate_entity_project(entity.project)
        return self.crud.artifact.update(entity)

    @_auto_refresh
    def delete_artifact(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete artifact from backend.

        See also
        -------
        digitalhub.delete_artifact
        """
        self.crud.artifact.delete(
            identifier=identifier,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )

    ##############################
    #  Dataitems
    ##############################

    @_auto_refresh
    def new_dataitem(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create a new dataitem.

        See also
        -------
        digitalhub.new_dataitem
        """
        return self.crud.dataitem.new(
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def log_dataitem(
        self,
        name: str,
        kind: str,
        source: str | None = None,
        data: Any | None = None,
        drop_existing: bool = False,
        extension: str | None = None,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create and upload a dataitem.

        See also
        -------
        digitalhub.log_dataitem
        """
        return self.crud.dataitem.log(
            name=name,
            kind=kind,
            path=path,
            source=source,
            data=data,
            drop_existing=drop_existing,
            extension=extension,
            **kwargs,
        )

    @_auto_refresh
    def log_generic_dataitem(
        self,
        name: str,
        source: str | None = None,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create and upload a generic dataitem.

        See also
        -------
        digitalhub.log_generic_dataitem
        """
        return self.crud.dataitem.log_generic(
            name=name,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    def log_table(
        self,
        name: str,
        source: str | None = None,
        data: Any | None = None,
        drop_existing: bool = False,
        path: str | None = None,
        file_format: str | None = None,
        read_df_params: dict | None = None,
        engine: str | None = None,
        **kwargs,
    ) -> Dataitem:
        """
        Create and upload a table dataitem.

        See also
        -------
        digitalhub.log_table
        """
        return self.crud.dataitem.log_table(
            name=name,
            path=path,
            source=source,
            data=data,
            drop_existing=drop_existing,
            file_format=file_format,
            read_df_params=read_df_params,
            engine=engine,
            **kwargs,
        )

    @_auto_refresh
    def get_dataitem(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Dataitem:
        """
        Get dataitem from backend.

        See also
        -------
        digitalhub.get_dataitem
        """
        return self.crud.dataitem.get(
            identifier=identifier,
            entity_id=entity_id,
        )

    @_auto_refresh
    def get_dataitem_versions(
        self,
        identifier: str,
    ) -> list[Dataitem]:
        """
        Get dataitem versions from backend.

        See also
        -------
        digitalhub.get_dataitem_versions
        """
        return self.crud.dataitem.get_versions(identifier=identifier)

    @_auto_refresh
    def list_dataitems(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
    ) -> list[Dataitem]:
        """
        List all latest version dataitems from backend.

        See also
        -------
        digitalhub.list_dataitems
        """
        return self.crud.dataitem.list(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            versions=versions,
        )

    @_auto_refresh
    def import_dataitem(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Dataitem:
        """
        Import dataitem into backend from a YAML file or key.

        See also
        -------
        digitalhub.import_dataitem
        """
        return self.crud.dataitem.import_entity(file=file, key=key, reset_id=reset_id)

    @_auto_refresh
    def update_dataitem(
        self,
        entity: Dataitem,
    ) -> Dataitem:
        """
        Update dataitem.

        See also
        -------
        digitalhub.update_dataitem
        """
        self._validate_entity_project(entity.project)
        return self.crud.dataitem.update(entity)

    @_auto_refresh
    def delete_dataitem(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete dataitem from backend.

        See also
        -------
        digitalhub.delete_dataitem
        """
        self.crud.dataitem.delete(
            identifier=identifier,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )

    ##############################
    #  Models
    ##############################

    @_auto_refresh
    def new_model(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create a new model.

        See also
        -------
        digitalhub.new_model
        """
        return self.crud.model.new(
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def log_model(
        self,
        name: str,
        kind: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload a model.

        See also
        -------
        digitalhub.log_model
        """
        return self.crud.model.log(
            name=name,
            kind=kind,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def log_generic_model(
        self,
        name: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload a generic model.

        See also
        -------
        digitalhub.log_generic_model
        """
        return self.crud.model.log_generic(
            name=name,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    def log_mlflow(
        self,
        name: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload a MLflow model.

        See also
        -------
        digitalhub.log_mlflow
        """
        return self.crud.model.log_mlflow(
            name=name,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    def log_sklearn(
        self,
        name: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload a scikit-learn model.

        See also
        -------
        digitalhub.log_sklearn
        """
        return self.crud.model.log_sklearn(
            name=name,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    def log_huggingface(
        self,
        name: str,
        source: str,
        drop_existing: bool = False,
        path: str | None = None,
        **kwargs,
    ) -> Model:
        """
        Create and upload a Huggingface model.

        See also
        -------
        digitalhub.log_huggingface
        """
        return self.crud.model.log_huggingface(
            name=name,
            source=source,
            drop_existing=drop_existing,
            path=path,
            **kwargs,
        )

    @_auto_refresh
    def get_model(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Model:
        """
        Get model from backend.

        See also
        -------
        digitalhub.get_model
        """
        return self.crud.model.get(
            identifier=identifier,
            entity_id=entity_id,
        )

    @_auto_refresh
    def get_model_versions(
        self,
        identifier: str,
    ) -> list[Model]:
        """
        Get model versions from backend.

        See also
        -------
        digitalhub.get_model_versions
        """
        return self.crud.model.get_versions(identifier=identifier)

    @_auto_refresh
    def list_models(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
    ) -> list[Model]:
        """
        List all latest version models from backend.

        See also
        -------
        digitalhub.list_models
        """
        return self.crud.model.list(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            versions=versions,
        )

    @_auto_refresh
    def import_model(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Model:
        """
        Import model into backend from a YAML file or key.

        See also
        -------
        digitalhub.import_model
        """
        return self.crud.model.import_entity(file=file, key=key, reset_id=reset_id)

    @_auto_refresh
    def update_model(
        self,
        entity: Model,
    ) -> Model:
        """
        Update model.

        See also
        -------
        digitalhub.update_model
        """
        self._validate_entity_project(entity.project)
        return self.crud.model.update(entity)

    @_auto_refresh
    def delete_model(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete model from backend.

        See also
        -------
        digitalhub.delete_model
        """
        self.crud.model.delete(
            identifier=identifier,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )

    ##############################
    #  Functions
    ##############################

    @_auto_refresh
    def new_function(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> Function:
        """
        Create a new function.

        See also
        -------
        digitalhub.new_function
        """
        return self.crud.function.new(
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            **kwargs,
        )

    @_auto_refresh
    def get_function(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Function:
        """
        Get function from backend.

        See also
        -------
        digitalhub.get_function
        """
        return self.crud.function.get(
            identifier=identifier,
            entity_id=entity_id,
        )

    @_auto_refresh
    def get_function_versions(
        self,
        identifier: str,
    ) -> list[Function]:
        """
        Get function versions from backend.

        See also
        -------
        digitalhub.get_function_versions
        """
        return self.crud.function.get_versions(identifier=identifier)

    @_auto_refresh
    def list_functions(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
    ) -> list[Function]:
        """
        List all latest version functions from backend.

        See also
        -------
        digitalhub.list_functions
        """
        return self.crud.function.list(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            versions=versions,
        )

    @_auto_refresh
    def import_function(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Function:
        """
        Import function into backend from a YAML file or key.

        See also
        -------
        digitalhub.import_function
        """
        return self.crud.function.import_entity(file=file, key=key, reset_id=reset_id)

    @_auto_refresh
    def update_function(
        self,
        entity: Function,
    ) -> Function:
        """
        Update function.

        See also
        -------
        digitalhub.update_function
        """
        self._validate_entity_project(entity.project)
        return self.crud.function.update(entity)

    @_auto_refresh
    def delete_function(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete function from backend.

        See also
        -------
        digitalhub.delete_function
        """
        self.crud.function.delete(
            identifier=identifier,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )

    ##############################
    #  Workflows
    ##############################

    @_auto_refresh
    def new_workflow(
        self,
        name: str,
        kind: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> Workflow:
        """
        Create a new workflow.

        See also
        -------
        digitalhub.new_workflow
        """
        return self.crud.workflow.new(
            name=name,
            kind=kind,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            **kwargs,
        )

    @_auto_refresh
    def get_workflow(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Workflow:
        """
        Get workflow from backend.

        See also
        -------
        digitalhub.get_workflow
        """
        return self.crud.workflow.get(
            identifier=identifier,
            entity_id=entity_id,
        )

    @_auto_refresh
    def get_workflow_versions(
        self,
        identifier: str,
    ) -> list[Workflow]:
        """
        Get workflow versions from backend.

        See also
        -------
        digitalhub.get_workflow_versions
        """
        return self.crud.workflow.get_versions(identifier=identifier)

    @_auto_refresh
    def list_workflows(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        versions: str | None = None,
    ) -> list[Workflow]:
        """
        List all latest version workflows from backend.

        See also
        -------
        digitalhub.list_workflows
        """
        return self.crud.workflow.list(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            versions=versions,
        )

    @_auto_refresh
    def import_workflow(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Workflow:
        """
        Import workflow into backend from a YAML file or key.

        See also
        -------
        digitalhub.import_workflow
        """
        return self.crud.workflow.import_entity(file=file, key=key, reset_id=reset_id)

    @_auto_refresh
    def update_workflow(
        self,
        entity: Workflow,
    ) -> Workflow:
        """
        Update workflow.

        See also
        -------
        digitalhub.update_workflow
        """
        self._validate_entity_project(entity.project)
        return self.crud.workflow.update(entity)

    @_auto_refresh
    def delete_workflow(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
        cascade: bool = True,
    ) -> None:
        """
        Delete workflow from backend.

        See also
        -------
        digitalhub.delete_workflow
        """
        self.crud.workflow.delete(
            identifier=identifier,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
            cascade=cascade,
        )

    ##############################
    #  Secrets
    ##############################

    @_auto_refresh
    def new_secret(
        self,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        secret_value: str | None = None,
        **kwargs,
    ) -> Secret:
        """
        Create a new secret.

        See also
        -------
        digitalhub.new_secret
        """
        return self.crud.secret.new(
            name=name,
            uuid=uuid,
            description=description,
            labels=labels,
            embedded=embedded,
            secret_value=secret_value,
            **kwargs,
        )

    @_auto_refresh
    def get_secret(
        self,
        identifier: str,
        entity_id: str | None = None,
    ) -> Secret:
        """
        Get secret from backend.

        See also
        -------
        digitalhub.get_secret
        """
        return self.crud.secret.get(
            identifier=identifier,
            entity_id=entity_id,
        )

    @_auto_refresh
    def list_secrets(
        self,
    ) -> list[Secret]:
        """
        List all latest version secrets from backend.

        See also
        -------
        digitalhub.list_secrets
        """
        return self.crud.secret.list()

    @_auto_refresh
    def import_secret(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = True,
    ) -> Secret:
        """
        Import secret into backend from a YAML file or key.

        See also
        -------
        digitalhub.import_secret
        """
        return self.crud.secret.import_entity(file=file, key=key, reset_id=reset_id)

    @_auto_refresh
    def update_secret(
        self,
        entity: Secret,
    ) -> Secret:
        """
        Update secret.

        See also
        -------
        digitalhub.update_secret
        """
        self._validate_entity_project(entity.project)
        return self.crud.secret.update(entity)

    @_auto_refresh
    def delete_secret(
        self,
        identifier: str,
        entity_id: str | None = None,
        delete_all_versions: bool = False,
    ) -> None:
        """
        Delete secret from backend.

        See also
        -------
        digitalhub.delete_secret
        """
        self.crud.secret.delete(
            identifier=identifier,
            entity_id=entity_id,
            delete_all_versions=delete_all_versions,
        )

    ##############################
    #  Runs
    ##############################

    @_auto_refresh
    def get_run(
        self,
        identifier: str,
    ) -> Run:
        """
        Get run from backend.

        See also
        -------
        digitalhub.get_run
        """
        return self.crud.run.get(
            identifier=identifier,
        )

    @_auto_refresh
    def list_runs(
        self,
        q: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        user: str | None = None,
        state: str | None = None,
        created: str | None = None,
        updated: str | None = None,
        function: str | None = None,
        workflow: str | None = None,
        task: str | None = None,
        action: str | None = None,
    ) -> list[Run]:
        """
        List all latest runs from backend.

        See also
        -------
        digitalhub.list_runs
        """
        return self.crud.run.list(
            q=q,
            name=name,
            kind=kind,
            user=user,
            state=state,
            created=created,
            updated=updated,
            function=function,
            workflow=workflow,
            task=task,
            action=action,
        )

    @_auto_refresh
    def delete_run(
        self,
        identifier: str,
        entity_id: str,
    ) -> None:
        """
        Delete run from backend.

        See also
        -------
        digitalhub.delete_run
        """
        self.crud.run.delete(
            identifier=identifier,
            entity_id=entity_id,
        )

    ##############################
    #  Project methods
    ##############################

    def run(self, workflow: str | None = None, **kwargs) -> Run:
        """
        Run workflow project.

        Parameters
        ----------
        workflow : str
            Workflow name.
        **kwargs : dict
            Keyword arguments passed to workflow.run().

        Returns
        -------
        Run
            Run instance.
        """
        self.refresh()

        workflow = workflow if workflow is not None else "main"

        for i in self.spec.workflows:
            if workflow in [i["name"], i["key"]]:
                entity = self.get_workflow(i["key"])
                break
        else:
            msg = f"Workflow {workflow} not found."
            raise EntityError(msg)

        return entity.run(**kwargs)

    def share(self, user: str) -> None:
        """
        Share project.

        Parameters
        ----------
        user : str
            User to share project with.
        Returns
        -------
        None
        """
        return base_processor.share_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            user=user,
            unshare=False,
        )

    def unshare(self, user: str) -> None:
        """
        Unshare project.

        Parameters
        ----------
        user : str
            User to unshare project with.
        Returns
        -------
        None
        """
        return base_processor.share_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            user=user,
            unshare=True,
        )
