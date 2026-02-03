# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.entities._base._base.entity import Base


class Extension(Base):
    """
    Set of extension metadata for an entity.
    """

    def __init__(
        self,
        name: str,
        id: str,
        kind: str,
        spec: dict[str, Any],
    ) -> None:
        self.name = name
        self.id = id
        self.kind = kind
        self.spec = spec

    @classmethod
    def from_dict(cls, obj: dict) -> Extension:
        """
        Return entity extension object from dictionary.

        Parameters
        ----------
        obj : dict
            A dictionary containing the attributes of the entity extension.

        Returns
        -------
        Extension
            An entity extension object.
        """
        return cls(**obj)
