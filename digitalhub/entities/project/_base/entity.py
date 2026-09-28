# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from pathlib import Path

from digitalhub.context.api import build_context
from digitalhub.entities._base.entity.entity import Entity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.processors import (
    base_crud_processor,
    base_special_ops_processor,
    crud_processor,
    executable_processor,
    search_processor,
)
from digitalhub.entities.project._base.protocol import ProjectListShortcuts
from digitalhub.factory.crud import bind_project_shortcut
from digitalhub.factory.entity import entity_factory
from digitalhub.factory.registry import registry
from digitalhub.stores.client.factory import get_client
from digitalhub.utils.exceptions import BackendError, EntityAlreadyExistsError, EntityError
from digitalhub.utils.io_utils import write_yaml
from digitalhub.utils.uri_utils import has_local_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities.artifact._base.entity import Artifact
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.entities.function._base.entity import Function
    from digitalhub.entities.model._base.entity import Model
    from digitalhub.entities.project._base.spec import ProjectSpec
    from digitalhub.entities.project._base.status import ProjectStatus
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.workflow._base.entity import Workflow


class Project(Entity, ProjectListShortcuts):
    """
    A class representing a project.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value
    _obj_attr = (*Entity._obj_attr, "id", "name", "extensions")
    _CONTEXT_ENTITY_SECTIONS = (
        f"{EntityTypes.ARTIFACT.value}s",
        f"{EntityTypes.DATAITEM.value}s",
        f"{EntityTypes.MODEL.value}s",
    )
    _EXECUTABLE_ENTITY_SECTIONS = (
        f"{EntityTypes.FUNCTION.value}s",
        f"{EntityTypes.WORKFLOW.value}s",
    )

    def __init__(
        self,
        name: str,
        kind: str,
        metadata: Metadata,
        spec: ProjectSpec,
        status: ProjectStatus,
        extensions: list[dict] | None = None,
        user: str | None = None,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.spec: ProjectSpec
        self.status: ProjectStatus
        self.extensions = extensions if extensions is not None else []

        self.id = name  # Unique identifier for the project
        self.name = name
        self.key = base_special_ops_processor.build_project_key(self.name)

        # Set client
        self._client = get_client()

        # Set context
        build_context(self)

    def __getattr__(self, name: str):
        """Resolve project-bound plugin shortcuts on first access."""
        try:
            shortcut_spec = registry.get_shortcut_spec(name)
        except AttributeError as e:
            raise AttributeError(name) from e
        if not shortcut_spec.project_bound:
            raise AttributeError(name)

        shortcut = bind_project_shortcut(
            registry.get_shortcut(name),
            self,
            refresh_project=shortcut_spec.refresh_project,
            validate_entity_project=shortcut_spec.validate_entity_project,
            inject_context=shortcut_spec.inject_context,
        )
        object.__setattr__(self, name, shortcut)
        return shortcut

    def __dir__(self) -> list[str]:
        """Include project-bound plugin shortcuts in completion."""
        return sorted(set(super().__dir__()) | set(registry.get_project_shortcut_names()))

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
            new_obj = base_crud_processor.update_project_entity(
                entity_type=self.ENTITY_TYPE,
                entity_name=self.name,
                entity_dict=self.to_dict(),
            )
        else:
            new_obj = base_crud_processor.create_project_entity(_entity=self)
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
        new_obj = base_crud_processor.read_project_entity(
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
        return search_processor.search_entity(
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
                    ent = crud_processor.read_context_entity(entity["key"])

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
                            if entity_type in self._CONTEXT_ENTITY_SECTIONS:
                                crud_processor.import_context_entity(file=ref, reset_id=reset_id, context=self.name)

                            elif entity_type in self._EXECUTABLE_ENTITY_SECTIONS:
                                executable_processor.import_executable_entity(
                                    file=ref, reset_id=reset_id, context=self.name
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
                        entity_factory.build_entity_from_dict(entity, entity_type=entity_type).save()
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
                if not embedded and ref is not None and has_local_scheme(ref):
                    try:
                        if entity_type in self._CONTEXT_ENTITY_SECTIONS:
                            crud_processor.load_context_entity(ref)

                        elif entity_type in self._EXECUTABLE_ENTITY_SECTIONS:
                            executable_processor.load_executable_entity(ref)

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
        return [*self._CONTEXT_ENTITY_SECTIONS, *self._EXECUTABLE_ENTITY_SECTIONS]

    ##############################
    #  Properties
    ##############################

    @property
    def functions(self) -> list[Function]:
        """
        Get all functions in the project.

        Returns
        -------
        list
            List of functions.
        """
        return self.list_functions()

    @property
    def workflows(self) -> list[Workflow]:
        """
        Get all workflows in the project.

        Returns
        -------
        list
            List of workflows.
        """
        return self.list_workflows()

    @property
    def artifacts(self) -> list[Artifact]:
        """
        Get all artifacts in the project.

        Returns
        -------
        list
            List of artifacts.
        """
        return self.list_artifacts()

    @property
    def dataitems(self) -> list[Dataitem]:
        """
        Get all dataitems in the project.

        Returns
        -------
        list
            List of dataitems.
        """
        return self.list_dataitems()

    @property
    def models(self) -> list[Model]:
        """
        Get all models in the project.

        Returns
        -------
        list
            List of models.
        """
        return self.list_models()

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
        return base_special_ops_processor.share_project_entity(
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
        return base_special_ops_processor.share_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            user=user,
            unshare=True,
        )
