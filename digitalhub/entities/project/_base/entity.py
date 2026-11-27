# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.entity.entity import PersistedEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.keys import build_project_key
from digitalhub.entities._mixin.extensions.mixin import ExtensionsMixin
from digitalhub.entities.project._base.processor import ProjectProcessor
from digitalhub.factory.crud import bind_project_shortcut
from digitalhub.factory.registry import registry

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities.artifact._base.entity import Artifact
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.entities.function._base.entity import Function
    from digitalhub.entities.model._base.entity import Model
    from digitalhub.entities.project._base.protocol import ProjectListShortcuts
    from digitalhub.entities.project._base.spec import ProjectSpec
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.workflow._base.entity import Workflow
else:

    class ProjectListShortcuts:
        pass


class Project(PersistedEntity, ProjectListShortcuts, ExtensionsMixin):
    """
    A class representing a project.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value
    _obj_attr = (*PersistedEntity._obj_attr, "id", "name", *ExtensionsMixin._obj_attr)

    def __init__(
        self,
        name: str,
        kind: str,
        metadata: Metadata,
        spec: ProjectSpec,
        status: Status,
        extensions: list[dict] | None = None,
        user: str | None = None,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.spec: ProjectSpec
        self.status: Status
        self._init_extensions(extensions)

        self.id = name  # Unique identifier for the project
        self.name = name
        self.key = build_project_key(self.name)

    def __getattr__(self, name: str):
        """Resolve project-bound plugin shortcuts on first access."""
        try:
            shortcut_spec = registry.get_shortcut_spec(name)
        except AttributeError as e:
            raise AttributeError(name) from e

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
        return sorted(set(super().__dir__()) | set(registry.get_shortcut_names()))

    ##############################
    #  Save / Refresh / Export
    ##############################

    def save(self, update: bool = False) -> Project:
        """
        Save entity into backend.

        Returns
        -------
        Project
            Entity saved.
        """
        if update:
            return self.update()
        return ProjectProcessor().create_project_entity(self)

    def update(self) -> Project:
        """
        Update entity into backend.

        Returns
        -------
        Project
            Entity updated.
        """
        return ProjectProcessor().update_project_entity(self)

    def refresh(self) -> Project:
        """
        Refresh object from backend.

        Returns
        -------
        Project
            Project object.
        """
        return ProjectProcessor().refresh_project_entity(self)

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
        return ProjectProcessor().search_entity(
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
        return ProjectProcessor().export_project_entity(self)

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
        # run() of the workflow entity, not of a processor: runtimes can override it.
        return ProjectProcessor().get_project_workflow(self, workflow).run(**kwargs)

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
        return ProjectProcessor().share_project_entity(
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
        return ProjectProcessor().share_project_entity(
            entity_type=self.ENTITY_TYPE,
            entity_name=self.name,
            user=user,
            unshare=True,
        )
