# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.trigger._base.entity import Trigger

if typing.TYPE_CHECKING:
    from digitalhub.entities.trigger.automl.spec import TriggerSpecAutoml
    from digitalhub.entities.trigger.automl.status import TriggerStatusAutoml


class TriggerAutoml(Trigger):
    """
    TriggerAutoml class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: TriggerSpecAutoml
        self.status: TriggerStatusAutoml
