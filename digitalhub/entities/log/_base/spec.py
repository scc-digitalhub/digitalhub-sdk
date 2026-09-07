# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class LogSpec(Spec):
    """
    LogSpec specifications.
    """

    def __init__(
        self,
        timestamp: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.timestamp = timestamp


class LogValidator(SpecValidator):
    """
    LogValidator validator.
    """

    timestamp: int | None = None
    """Timestamp of the log."""
