# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.builder import EntityBuilder


class UnversionedBuilder(EntityBuilder):
    """
    Helper builder for entities whose name is derived from the identifier.
    """

    def _parse_dict(self, obj: dict) -> dict:
        """
        Add the project and the identifier to the common fields.

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
            "uuid": self.build_uuid(obj.get("id")),
        }
