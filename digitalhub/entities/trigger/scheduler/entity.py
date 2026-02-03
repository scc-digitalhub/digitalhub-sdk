# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.trigger._base.entity import Trigger

if typing.TYPE_CHECKING:
    from digitalhub.entities.trigger.scheduler.spec import TriggerSpecScheduler
    from digitalhub.entities.trigger.scheduler.status import TriggerStatusScheduler


class TriggerScheduler(Trigger):
    """
    TriggerScheduler class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: TriggerSpecScheduler
        self.status: TriggerStatusScheduler
