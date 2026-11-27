# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextlib
import typing
from pathlib import Path
from typing import Any, ClassVar
from warnings import warn

from digitalhub.context.api import build_context, delete_context
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.keys import EntityKey
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities._processors.utils import get_context
from digitalhub.factory.entity import entity_factory
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import DeleteOptions, NoOptions, SearchOptions, ShareOptions
from digitalhub.stores.client.compiler.targets import BaseCollectionTarget, BaseEntityTarget, ContextProjectTarget
from digitalhub.stores.client.factory import resolve_client
from digitalhub.utils.exceptions import BackendError, EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.io_utils import read_yaml, write_yaml
from digitalhub.utils.logger.logger import get_logger
from digitalhub.utils.uri_utils import has_local_scheme

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.project._base.entity import Project
    from digitalhub.entities.workflow._base.entity import Workflow

logger = get_logger(__name__)


class ProjectProcessor:
    """Backend operations of projects: CRUD, import/export, sharing and search of their entities."""

    # Sections of the project spec that list entities, and the type of each.
    _CONTEXT_ENTITY_SECTIONS = (
        f"{EntityTypes.ARTIFACT.value}s",
        f"{EntityTypes.DATAITEM.value}s",
        f"{EntityTypes.MODEL.value}s",
    )
    _EXECUTABLE_ENTITY_SECTIONS = (
        f"{EntityTypes.FUNCTION.value}s",
        f"{EntityTypes.WORKFLOW.value}s",
    )
    _ENTITY_SECTION_TO_TYPE: ClassVar[dict[str, str]] = {
        "artifacts": EntityTypes.ARTIFACT.value,
        "dataitems": EntityTypes.DATAITEM.value,
        "models": EntityTypes.MODEL.value,
        "functions": EntityTypes.FUNCTION.value,
        "workflows": EntityTypes.WORKFLOW.value,
    }

    def __init__(self, crud_processor: ContextEntityCRUDProcessor | None = None) -> None:
        self.crud_processor = ContextEntityCRUDProcessor() if crud_processor is None else crud_processor

    @staticmethod
    def _registered(obj: dict) -> Project:
        """
        Build a project from backend state and register its context.

        Contexts change only here, with what the backend returned: building a
        project elsewhere, from a listing or a YAML file, leaves them alone.
        """
        project = typing.cast("Project", entity_factory.build_entity_from_dict(obj))
        build_context(project)
        return project

    def create_project_entity(self, project: Project) -> Project:
        """Create ``project`` in the backend, register its context and update it with the stored state."""
        stored = resolve_client().execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.CREATE,
                target=BaseCollectionTarget(project.ENTITY_TYPE),
                payload=project.to_dict(),
            )
        )
        project._update_attributes(self._registered(stored))
        return project

    def create_project_entity_from_params(self, **kwargs) -> Project:
        """Build a project from parameters, then create it."""
        return self.create_project_entity(typing.cast("Project", entity_factory.build_entity_from_params(**kwargs)))

    def read_project_entity(self, entity_type: str, entity_name: str) -> Project:
        """Read a project from the backend and register its context."""
        stored = resolve_client().execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.READ,
                target=BaseEntityTarget(entity_type, entity_name),
            )
        )
        return self._registered(stored)

    def refresh_project_entity(self, project: Project) -> Project:
        """Update ``project`` with the backend state."""
        project._update_attributes(self.read_project_entity(project.ENTITY_TYPE, project.name))
        return project

    def list_project_entities(self, entity_type: str) -> list[Project]:
        """List the projects; listing registers no context."""
        stored = resolve_client().execute_list(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.LIST,
                target=BaseCollectionTarget(entity_type),
            )
        )
        return [typing.cast("Project", entity_factory.build_entity_from_dict(obj)) for obj in stored]

    def import_project_entity(self, file: str, **kwargs) -> Project:
        obj: dict = read_yaml(file)
        obj["status"] = {}
        ent: Project = entity_factory.build_entity_from_dict(obj)
        reset_id = kwargs.pop("reset_id", False)

        try:
            self.create_project_entity(ent)
        except EntityAlreadyExistsError:
            msg = f"Entity {ent.name} already exists."
            if reset_id:
                self.read_project_entity(ent.ENTITY_TYPE, ent.name)
                self._import_entities(ent.name, obj, reset_id=reset_id)
                warn(f"{msg} Other entities ids have been imported.")
                return self.refresh_project_entity(ent)
            raise EntityError(f"{msg} If you want to update it, use load instead.")

        self._import_entities(ent.name, obj, reset_id=reset_id)
        return self.refresh_project_entity(ent)

    def load_project_entity(self, file: str) -> Project:
        obj: dict = read_yaml(file)
        ent: Project = entity_factory.build_entity_from_dict(obj)

        try:
            self.update_project_entity(ent)
        except EntityNotExistsError:
            self.create_project_entity(ent)

        self._load_entities(obj)
        return self.refresh_project_entity(ent)

    def export_project_entity(self, project: Project) -> str:
        """
        Write the project as YAML in its source folder.

        Entities that are not embedded in the project are exported to their own
        files, and the project keeps a reference to each file.
        """
        obj = self._export_not_embedded(self._refresh_to_dict(project))
        root = Path(project.spec.source)
        root.mkdir(parents=True, exist_ok=True)
        pth = root / f"{project.ENTITY_TYPE}s-{project.name}.yaml"
        write_yaml(pth, obj)
        return str(pth)

    def _refresh_to_dict(self, project: Project) -> dict:
        """Return the project with the entities the backend lists, or as it is if the backend cannot be read."""
        with contextlib.suppress(BackendError):
            self.refresh_project_entity(project)
        return project.to_dict()

    def _export_not_embedded(self, obj: dict) -> dict:
        """Export the entities that are not embedded and store a reference to their file."""
        for entity_type in self._get_entity_types():
            for idx, entity in enumerate(obj.get("spec", {}).get(entity_type, [])):
                if not self._is_embedded(entity):
                    ent = self.crud_processor.read_context_entity(entity["key"])
                    # export() of the entity, not of the CRUD processor:
                    # executables write their source file too.
                    obj["spec"][entity_type][idx]["metadata"]["ref"] = ent.export()
        return obj

    def _import_entities(self, project: str, obj: dict, reset_id: bool = False) -> None:
        """Create in ``project`` the entities listed in a project file."""
        for entity_type in self._get_entity_types():
            for entity in obj.get("spec", {}).get(entity_type, []):
                embedded = self._is_embedded(entity)
                ref = entity["metadata"].get("ref")

                # Not embedded: import the entity from its own file.
                if not embedded and ref is not None:
                    if has_local_scheme(ref):
                        try:
                            if entity_type in self._CONTEXT_ENTITY_SECTIONS:
                                self.crud_processor.import_context_entity(file=ref, reset_id=reset_id, context=project)
                            elif entity_type in self._EXECUTABLE_ENTITY_SECTIONS:
                                ContextEntityExecutableProcessor(self.crud_processor).import_executable_entity(
                                    file=ref, reset_id=reset_id, context=project
                                )
                        except FileNotFoundError:
                            raise EntityError(f"File not found: {ref}.")

                # Embedded: create it from the project file.
                elif embedded:
                    # The embedded field may be missing from the metadata.
                    if entity["metadata"].get("embedded") is None:
                        entity["metadata"]["embedded"] = True

                    if reset_id:
                        new_id = build_uuid()
                        entity["id"] = new_id
                        entity["metadata"]["version"] = new_id

                    try:
                        entity_type_name = self._ENTITY_SECTION_TO_TYPE[entity_type]
                        self.crud_processor.create_context_entity(
                            entity_factory.build_entity_from_dict(entity, entity_type=entity_type_name)
                        )
                    except EntityAlreadyExistsError:
                        pass

    def _load_entities(self, obj: dict) -> None:
        """Create or update the entities that a project file references by file."""
        for entity_type in self._get_entity_types():
            for entity in obj.get("spec", {}).get(entity_type, []):
                ref = entity["metadata"].get("ref")
                if not self._is_embedded(entity) and ref is not None and has_local_scheme(ref):
                    try:
                        if entity_type in self._CONTEXT_ENTITY_SECTIONS:
                            self.crud_processor.load_context_entity(ref)
                        elif entity_type in self._EXECUTABLE_ENTITY_SECTIONS:
                            ContextEntityExecutableProcessor(self.crud_processor).load_executable_entity(ref)
                    except FileNotFoundError:
                        raise EntityError(f"File not found: {ref}.")

    @staticmethod
    def _is_embedded(entity: dict) -> bool:
        """Whether the project file contains the entity itself, not a reference to its file."""
        metadata_embedded = entity["metadata"].get("embedded", False)
        no_status = entity.get("status", None) is None
        no_spec = entity.get("spec", None) is None
        return metadata_embedded or not (no_status and no_spec)

    def _get_entity_types(self) -> list[str]:
        """Sections of the project spec that list entities."""
        return [*self._CONTEXT_ENTITY_SECTIONS, *self._EXECUTABLE_ENTITY_SECTIONS]

    def update_project_entity(self, project: Project) -> Project:
        """Update ``project`` in the backend, register its context and update it with the stored state."""
        stored = resolve_client().execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.UPDATE,
                target=BaseEntityTarget(project.ENTITY_TYPE, project.name),
                payload=project.to_dict(),
            )
        )
        project._update_attributes(self._registered(stored))
        return project

    def delete_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        cascade: bool = True,
        clean_context: bool = True,
    ) -> dict:
        """Delete a project; its context is removed only after the backend deleted it."""
        response = resolve_client().execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.DELETE,
                target=BaseEntityTarget(entity_type, entity_name),
                options=DeleteOptions(cascade=cascade),
            )
        )
        if clean_context:
            delete_context(entity_name)
        return response

    def get_project_workflow(self, project: Project, workflow: str | None = None) -> Workflow:
        """Refresh ``project`` and return its workflow with this name or key, ``main`` by default."""
        self.refresh_project_entity(project)
        workflow = "main" if workflow is None else workflow
        for entry in project.spec.workflows:
            if workflow in (entry["name"], entry["key"]):
                return typing.cast(
                    "Workflow",
                    self.crud_processor.read_context_entity(
                        entry["key"], entity_type=EntityTypes.WORKFLOW.value, project=project.name
                    ),
                )
        raise EntityError(f"Workflow {workflow} not found.")

    def share_project_entity(
        self,
        entity_type: str,
        entity_name: str,
        user: str,
        unshare: bool = False,
        role: str | None = None,
    ) -> None:
        client = resolve_client()
        target = BaseEntityTarget(entity_type, entity_name)
        entity_id = None

        if unshare:
            users = client.execute(
                ClientOp(
                    category=ApiType.BASE,
                    operation=BackendOp.SHARE_READ,
                    target=target,
                    options=NoOptions(),
                )
            )
            for u in users:
                if u["user"] == user:
                    entity_id = u["id"]
                    break
            else:
                raise ValueError(f"User '{user}' does not have access to project.")

        options = ShareOptions(user=user, unshare=unshare, share_id=entity_id, role=role)
        if unshare:
            client.execute(
                ClientOp(
                    category=ApiType.BASE,
                    operation=BackendOp.UNSHARE,
                    target=target,
                    options=options,
                )
            )
            return
        client.execute(
            ClientOp(
                category=ApiType.BASE,
                operation=BackendOp.SHARE,
                target=target,
                options=options,
                payload={},
            )
        )

    def search_entity(
        self,
        project: str,
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
        context = get_context(project)
        params = {**kwargs}
        if query is not None:
            params["query"] = query
        if entity_types is not None:
            params["entity_types"] = entity_types
        if name is not None:
            params["name"] = name
        if kind is not None:
            params["kind"] = kind
        if created is not None:
            params["created"] = created
        if updated is not None:
            params["updated"] = updated
        if description is not None:
            params["description"] = description
        if labels is not None:
            params["labels"] = labels
        entities = context.client.execute_list(
            ClientOp(
                category=ApiType.CONTEXT,
                operation=BackendOp.SEARCH,
                target=ContextProjectTarget(context.name),
                options=SearchOptions(**params),
            )
        )
        living_entities = []
        dead_entities = []
        for entity in entities:
            try:
                entity_type = EntityKey.parse(entity["key"]).entity_type
                if self._has_full_entity_data(entity):
                    living_entity = entity_factory.build_entity_from_dict(entity, entity_type=entity_type)
                else:
                    living_entity = self.crud_processor.read_context_entity(
                        entity["key"],
                        entity_type=entity_type,
                    )
                living_entities.append(living_entity)
            except BackendError:
                logger.debug(
                    f"Entity '{entity.get('key', 'unknown')}' could not be read from backend",
                    exc_info=True,
                )
                dead_entities.append(entity)
        return living_entities, dead_entities

    @staticmethod
    def _has_full_entity_data(entity: dict[str, Any]) -> bool:
        """Check whether search returned enough data to build an entity without a read."""
        identity_fields = ("key", "kind", "id", "name", "project")
        return (
            all(entity.get(field) for field in identity_fields)
            and isinstance(entity.get("metadata", {}), dict)
            and isinstance(entity.get("spec"), dict)
            and isinstance(entity.get("status", {}), dict)
        )
