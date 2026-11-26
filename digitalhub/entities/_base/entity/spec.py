# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar

from digitalhub.entities._base._base.section import EntitySection


class Spec(EntitySection):
    """
    A class representing the specifications of an entity.
    Specifications are a collection of information about an entity
    thought to be immutable by the user.
    """

    ALLOW_EXTRA_INPUTS: ClassVar[bool] = False
