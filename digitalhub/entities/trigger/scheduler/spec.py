# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.trigger._base.spec import TriggerSpec


class TriggerSpecScheduler(TriggerSpec):
    """
    TriggerSpecScheduler specifications.
    """

    schedule: str
    """Quartz cron expression."""
