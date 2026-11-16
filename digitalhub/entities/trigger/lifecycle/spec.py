# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities.trigger._base.spec import TriggerSpec

regexp = r"store://([^/]+)/(.+)"


class TriggerSpecLifecycle(TriggerSpec):
    """
    TriggerSpecLifecycle specifications.
    """

    key: str | None = Field(pattern=regexp)
    """Entity key."""

    states: list[str] = None
    """List of entity states."""
