# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._commons.keys import EntityRef
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin
from digitalhub.entities.task._base.processor import TaskProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities.run._base.entity import Run


class Task(ContextEntity, UnversionedMixin):
    """
    A class representing a task.
    """

    ENTITY_TYPE = EntityTypes.TASK.value

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata,
        spec,
        status,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_unversioned_identity(project, uuid, kind)
        self.spec: Spec
        self.status: Status

    ##############################
    #  Task methods
    ##############################

    def run(
        self,
        run_kind: str,
        save: bool = True,
        **kwargs,
    ) -> Run:
        """
        Run task.

        Parameters
        ----------
        run_kind : str
            Kind the object.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        Run
            Run object.
        """
        return TaskProcessor().build_run(self, run_kind, save=save, **kwargs)

    def _get_task_string(self) -> str:
        """
        Get task string.

        Returns
        -------
        str
            Task string.
        """
        return str(EntityRef(self.kind, self.project, id=self.id))
