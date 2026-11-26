# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from digitalhub.entities._base._base.section import EntitySection


class Metadata(EntitySection):
    """
    A class representing the metadata of an entity.
    Metadata is a collection of information about an entity thought
    to be modifiable by the user. The information contained in the
    metadata can be discordant with the actual state of the entity,
    for example the name of the entity in the database.
    """

    project: str | None = None
    name: str | None = None
    version: str | None = None
    description: str | None = None
    labels: list[str] | None = None
    created: str | None = None
    created_by: str | None = None
    updated: str | None = None
    updated_by: str | None = None
    embedded: bool | None = None
    relationships: list[dict] | None = None
    ref: str | None = None


class RelationshipValidator(BaseModel):
    """
    A class representing the relationship of an entity.
    """

    model_config = ConfigDict(use_enum_values=True)

    type_: str = Field(default=None, alias="type")
    source: str = None
    dest: str = None
