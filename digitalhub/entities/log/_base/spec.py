# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar

from digitalhub.entities._base.entity.spec import Spec


class LogSpec(Spec):
    """
    LogSpec specifications.
    """

    ALLOW_EXTRA_INPUTS: ClassVar[bool] = True

    timestamp: int | None = None
    """Timestamp of the log."""
