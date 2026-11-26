# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.builder import EntityBuilder
from digitalhub.entities._base.entity.status import Status
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.project._base.spec import ProjectSpec


class ProjectProjectBuilder(EntityBuilder):
    """
    ProjectProject builder.
    """

    ENTITY_TYPE = EntityTypes.PROJECT.value
    ENTITY_CLASS = Project
    ENTITY_SPEC_CLASS = ProjectSpec
    ENTITY_STATUS_CLASS = Status
    ENTITY_KIND = EntityKinds.PROJECT_PROJECT.value

    def build(
        self,
        name: str,
        kind: str,
        description: str | None = None,
        labels: list[str] | None = None,
        config: dict | None = None,
        context: str | None = None,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Project:
        """
        Create a new object.

        Parameters
        ----------
        name : str
            Object name.
        kind : str
            Kind the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        config : dict
            DHCore environment configuration.
        context : str
            The context local folder of the project.
        extensions : list[dict]
            List of extensions to apply.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Project
            Object instance.
        """
        name = self.build_name(name)
        metadata = self.build_metadata(
            project=name,
            name=name,
            description=description,
            labels=labels,
        )
        spec = self.build_spec(
            config=config,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            name=name,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
            extensions=extensions,
        )

    def _parse_dict(self, obj: dict) -> dict:
        """
        Add the name and the extensions to the common fields.

        Parameters
        ----------
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            Keyword arguments of the entity constructor.
        """
        return {
            **super()._parse_dict(obj),
            "name": self.build_name(obj.get("name")),
            "extensions": obj.get("extensions", []),
        }
