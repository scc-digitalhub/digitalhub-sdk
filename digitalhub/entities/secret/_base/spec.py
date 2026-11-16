# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec


class SecretSpec(Spec):
    """
    SecretSpec specifications.
    """

    path: str | None = None
    """Path to the secret."""

    provider: str | None = None
    """Provider of the secret."""
