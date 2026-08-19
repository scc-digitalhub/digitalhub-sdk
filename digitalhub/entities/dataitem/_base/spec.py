# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._mixin.material.spec import MaterialSpec, MaterialValidator


class DataitemSpec(MaterialSpec):
    """
    DataitemSpec specifications.
    """


class DataitemValidator(MaterialValidator):
    """
    DataitemValidator validator.
    """
