# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities._mixin.material.spec import MaterialSpec
from digitalhub.entities.dataitem.table.models import TableSchema


class DataitemSpecTable(MaterialSpec):
    """
    DataitemSpecTable specifications.
    """

    schema_: TableSchema | None = Field(default=None, alias="schema")
    """The schema of the dataitem in table schema format."""
