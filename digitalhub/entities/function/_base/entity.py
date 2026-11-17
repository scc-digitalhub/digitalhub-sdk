# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.executable.mixin import ExecutableMixin
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.processors import run_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.function._base.spec import FunctionSpec
    from digitalhub.entities.function._base.status import FunctionStatus
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task


class Function(ContextEntity, VersionedMixin, ExecutableMixin):
    """
    A class representing a function.
    """

    ENTITY_TYPE = EntityTypes.FUNCTION.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata,
        spec,
        status,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_versioned_identity(project, name, uuid, kind)

        self.spec: FunctionSpec
        self.status: FunctionStatus

    ##############################
    #  Function Methods
    ##############################

    def run(
        self,
        action: str,
        wait: bool = False,
        log_info: bool = True,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> Run:
        """
        Run function. This method creates a new run and executes it.

        Parameters
        ----------
        action : str
            Action to execute.
        wait : bool
            Flag to wait for execution.
        log_info : bool
            Flag to log information while waiting.
        extensions : list[dict] | None
            List of extensions to apply.
        **kwargs : dict
            Keyword arguments passed to Run builder.

        Returns
        -------
        Run
            Run instance.
        """
        # Create or update new task
        task: Task = self._get_or_create_task(action)

        run = self._create_run(task, action, extensions=extensions, **kwargs)
        return run_processor.execute_run(run, wait=wait, log_info=log_info)
