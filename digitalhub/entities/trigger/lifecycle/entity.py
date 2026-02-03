# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.trigger._base.entity import Trigger

if typing.TYPE_CHECKING:
    from digitalhub.entities.trigger.lifecycle.spec import TriggerSpecLifecycle
    from digitalhub.entities.trigger.lifecycle.status import TriggerStatusLifecycle


class TriggerLifecycle(Trigger):
    """
    TriggerLifecycle class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: TriggerSpecLifecycle
        self.status: TriggerStatusLifecycle
