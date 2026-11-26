# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.executable.run import ExecutableRunMixin
from digitalhub.entities._mixin.executable.task import ExecutableTaskMixin
from digitalhub.entities._mixin.executable.trigger import ExecutableTriggerMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class ExecutableMixin(ExecutableTaskMixin, ExecutableRunMixin, ExecutableTriggerMixin):
    def run(
        self,
        action: str,
        wait: bool = False,
        log_info: bool = True,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """Create and execute a run for an executable action.

        Parameters
        ----------
        action : str
            Action to execute.
        wait : bool
            Flag to wait for execution to finish.
        log_info : bool
            Flag to log information while waiting.
        extensions : list[dict] | None
            List of extensions to apply.
        **kwargs : dict
            Keyword arguments passed to Run construction.

        Returns
        -------
        Run
            Executed run.
        """
        return ContextEntityExecutableProcessor().execute_executable(
            self,
            action,
            wait=wait,
            log_info=log_info,
            extensions=extensions,
            **kwargs,
        )
