# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from digitalhub.utils.generic_utils import dump_json


class Spec(BaseModel):
    """
    A class representing the specifications.of an entity.
    specifications.is a collection of information about an entity
    thought to be immutable by the user.
    """

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    ALLOW_EXTRA_INPUTS: ClassVar[bool] = False

    @classmethod
    def from_dict(cls, obj: dict) -> Spec:
        """
        Return entity specifications.object from dictionary.

        Parameters
        ----------
        obj : dict
            A dictionary containing the attributes of the entity specifications.

        Returns
        -------
        EntitySpec
            An entity specifications.object.
        """
        return cls.model_validate(obj)

    def to_dict(self) -> dict:
        """Return the spec as a dictionary using the SDK serialization rules."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_json(self) -> str:
        """Return the spec as JSON."""
        return dump_json(self.to_dict())

    def __repr__(self) -> str:
        return str(self.to_dict())
