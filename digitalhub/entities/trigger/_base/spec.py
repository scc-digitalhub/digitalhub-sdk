# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec


class TriggerSpec(Spec):
    """
    TriggerSpec specifications.
    """

    task: str
    """Task string."""

    template: dict
    """Template map."""

    function: str | None = None
    """Function string."""

    workflow: str | None = None
    """Workflow string."""
