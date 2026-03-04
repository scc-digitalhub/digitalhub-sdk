# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class ExtensionSpec(Spec):
    """
    ExtensionSpec specifications.
    """

    def __init__(
        self,
        schema: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.schema = schema


class ExtensionValidator(SpecValidator):
    """
    ExtensionValidator validator.
    """

    schema_: str = Field(alias="schema")
    """Schema of the extension."""
