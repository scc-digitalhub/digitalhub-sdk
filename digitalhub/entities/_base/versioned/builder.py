# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.entity.builder import EntityBuilder

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.versioned.entity import VersionedEntity


class VersionedBuilder(EntityBuilder):
    """
    Versioned builder.
    """

    def from_dict(self, obj: dict) -> VersionedEntity:
        """
        Create a new object from dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to create object from.

        Returns
        -------
        VersionedEntity
            Object instance.
        """
        parsed_dict = self._parse_dict(obj)
        return self.build_entity(**parsed_dict)

    def _parse_dict(self, obj: dict) -> dict:
        """
        Get dictionary and parse it to a valid entity dictionary.

        Parameters
        ----------
        entity : str
            Entity type.
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        project = obj.get("project")
        kind = obj.get("kind")
        name = self.build_name(obj.get("name"))
        uuid = self.build_uuid(obj.get("id"))
        metadata = self.build_metadata(**obj.get("metadata", {}))
        spec = self.build_spec(**obj.get("spec", {}))
        status = self.build_status(**obj.get("status", {}))
        user = obj.get("user")
        return {
            "project": project,
            "name": name,
            "uuid": uuid,
            "kind": kind,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "user": user,
        }
