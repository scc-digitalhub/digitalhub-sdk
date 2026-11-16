# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field, field_validator

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities.project._base.models import ProfileConfig


class ProjectSpec(Spec):
    """
    ProjectSpec specifications.
    """

    source: str = "./"
    """The project's source."""

    functions: list = Field(default_factory=list)
    """List of project's functions."""

    artifacts: list = Field(default_factory=list)
    """List of project's artifacts."""

    workflows: list = Field(default_factory=list)
    """List of project's workflows."""

    dataitems: list = Field(default_factory=list)
    """List of project's dataitems."""

    models: list = Field(default_factory=list)
    """List of project's models."""

    config: ProfileConfig | dict = Field(default_factory=dict)
    """Project's config."""

    @field_validator("config", mode="before")
    @classmethod
    def normalize_config(cls, value: ProfileConfig | dict | None) -> dict:
        if value is None:
            return {}
        if isinstance(value, ProfileConfig):
            return value.model_dump(by_alias=True, exclude_none=True)
        return ProfileConfig.model_validate(value).model_dump(by_alias=True, exclude_none=True)
