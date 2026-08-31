# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod

from digitalhub.entities._mixin.executable.run import ExecutableRunMixin
from digitalhub.entities._mixin.executable.task import ExecutableTaskMixin
from digitalhub.entities._mixin.executable.trigger import ExecutableTriggerMixin

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class ExecutableMixin(ExecutableTaskMixin, ExecutableRunMixin, ExecutableTriggerMixin):
    @abstractmethod
    def run(self, *args, **kwargs) -> Run:
        """Create and execute a run.

        Parameters
        ----------
        *args
            Positional run parameters.
        **kwargs : dict
            Keyword run parameters.

        Returns
        -------
        Run
            Executed run.
        """
        raise NotImplementedError
