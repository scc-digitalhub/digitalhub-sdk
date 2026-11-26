# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing_extensions import Self

from digitalhub.utils.generic_utils import dump_json


class EntitySection(BaseModel):
    """
    Base class for the metadata, spec and status of an entity.

    Unknown fields are kept, so fields added by a newer backend survive
    a read followed by a save.
    """

    model_config = ConfigDict(extra="allow", use_enum_values=True)

    @classmethod
    def from_dict(cls, obj: dict) -> Self:
        """Build the section from a dictionary."""
        return cls.model_validate(obj)

    def to_dict(self) -> dict:
        """Return the section as a dictionary, without empty fields."""
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_json(self) -> str:
        """Return the section as JSON."""
        return dump_json(self.to_dict())

    def __repr__(self) -> str:
        return str(self.to_dict())
