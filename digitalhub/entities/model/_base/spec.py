# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._mixin.material.spec import MaterialSpec


class ModelSpec(MaterialSpec):
    """
    ModelSpec specifications.
    """

    framework: str | None = None
    """Model framework (e.g. 'pytorch')."""

    algorithm: str | None = None
    """Model algorithm (e.g. 'resnet')."""

    parameters: dict | None = None
    """Model validator."""
