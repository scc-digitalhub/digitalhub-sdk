# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.entity.builder import EntityBuilder

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity


class VersionedBuilder(EntityBuilder):
    """
    Helper builder for entities with versioned identity fields.
    """

    def build(
        self,
        kind: str,
        project: str,
        name: str,
        *,
        uuid: str | None = None,
        version: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> ContextEntity:
        """
        Create a new object.

        Parameters
        ----------
        kind : str
            Kind the object.
        project : str
            Project name.
        name : str
            Object name.
        uuid : str
            ID of the object.
        version : str
            Version stored in entity metadata.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        ContextEntity
            Object instance.
        """
        name = self.build_name(name)
        metadata = self.build_metadata(
            project=project,
            name=name,
            version=version,
            description=description,
            labels=labels,
            embedded=embedded,
        )
        return self.build_entity(
            project=project,
            name=name,
            uuid=self.build_uuid(uuid),
            kind=kind,
            metadata=metadata,
            spec=self.build_spec(**kwargs),
            status=self.build_status(),
        )

    def _parse_dict(self, obj: dict) -> dict:
        """
        Add the project, the name and the identifier to the common fields.

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
            "project": obj.get("project"),
            "name": self.build_name(obj.get("name")),
            "uuid": self.build_uuid(obj.get("id")),
        }
