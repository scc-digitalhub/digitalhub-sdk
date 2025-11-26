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
        run: str,
        timestamp: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.run = run
        self.timestamp = timestamp


class LogValidator(SpecValidator):
    """
    LogValidator validator.
    """

    run: str
    """Run id."""

    timestamp: int | None = None
    """Timestamp of the log."""
