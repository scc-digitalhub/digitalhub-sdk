# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin
from digitalhub.entities._processors.processors import run_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.spec import TaskSpec
    from digitalhub.entities.task._base.status import TaskStatus


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
        self.spec: TaskSpec
        self.status: TaskStatus

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
        return run_processor.build_task_run(self, run_kind, save=save, **kwargs)

    def _get_task_string(self) -> str:
        """
        Get task string.

        Returns
        -------
        str
            Task string.
        """
        return f"{self.kind}://{self.project}/{self.id}"

    ##############################
    # CRUD Methods for Run
    ##############################

    def new_run(self, save: bool = True, **kwargs) -> Run:
        """
        Create a new run.

        Parameters
        ----------
        save : bool
            Flag to indicate save.
        **kwargs : dict
            Keyword arguments to build run. See new_run().

        Returns
        -------
        Run
            Run object.
        """
        return run_processor.create_run(save=save, **kwargs)

    def get_run(self, entity_key: str) -> Run:
        """
        Get run.

        Parameters
        ----------
        entity_key : str
            Entity key.

        Returns
        -------
        Run
            Run object.
        """
        return run_processor.get_run(entity_key)

    def delete_run(self, entity_key: str) -> dict:
        """
        Delete run.

        Parameters
        ----------
        entity_key : str
            Entity key.

        Returns
        -------
        dict
            Response from backend.
        """
        return run_processor.delete_run(entity_key)
