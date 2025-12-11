# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
import typing

from digitalhub.entities._base.metrics.entity import MetricsEntity
from digitalhub.entities._base.unversioned.entity import UnversionedEntity
from digitalhub.entities._commons.enums import EntityTypes, State
from digitalhub.entities._processors.processors import context_processor
from digitalhub.factory.entity import entity_factory
from digitalhub.factory.runtime import runtime_factory
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.logger import LOGGER

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.log._base.entity import Log
    from digitalhub.entities.run._base.spec import RunSpec
    from digitalhub.entities.run._base.status import RunStatus
    from digitalhub.runtimes._base import Runtime


class Run(UnversionedEntity, MetricsEntity):
    """
    A class representing a run.
    """

    ENTITY_TYPE = EntityTypes.RUN.value

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpec,
        status: RunStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, uuid, kind, metadata, spec, status, user)

        self.spec: RunSpec
        self.status: RunStatus

    ##############################
    #  Run Methods
    ##############################

    def build(self) -> None:
        """
        Build run.
        """
        executable = self._get_executable()
        task = self._get_task()
        new_spec = self._get_runtime().build(executable, task, self.to_dict())
        self.spec = entity_factory.build_spec(self.kind, **new_spec)
        self.status.state = State.BUILT.value
        self.save(update=True)

    def run(self) -> Run:
        """
        Run run.

        Returns
        -------
        Run
            Run object.
        """
        self.refresh()

        self.start_execution()
        self._setup_execution()

        try:
            status = self._get_runtime().run(self.to_dict())

        # Handle exceptions and set run status and message
        except Exception as e:
            self.refresh()
            if self.spec.local_execution:
                self.status.state = State.ERROR.value
            self.status.message = str(e)
            self.save(update=True)
            raise e

        # Unset run in context
        finally:
            self.end_execution()

        self.refresh()
        if not self.spec.local_execution:
            status.pop("state", None)
        new_status = {**self.status.to_dict(), **status}
        self.set_status(new_status)
        self.save(update=True)
        return self

    def wait(self, log_info: bool = True) -> Run:
        """
        Wait for run to finish.

        Parameters
        ----------
        log_info : bool
            If True, log information.

        Returns
        -------
        Run
            Run object.
        """
        start = time.time()
        while True:
            if log_info:
                LOGGER.info(f"Waiting for run {self.id} to finish...")
            self.refresh()
            time.sleep(5)
            if self.status.state in [
                State.STOPPED.value,
                State.ERROR.value,
                State.COMPLETED.value,
            ]:
                if log_info:
                    current = time.time() - start
                    LOGGER.info(f"Run {self.id} finished in {current:.2f} seconds.")
                return self

    def logs(self) -> list[Log]:
        """
        Get run logs. If no logs are present, an empty list is returned.
        In case of local execution, logs are printed to console.

        Returns
        -------
        list[Log]
            List of run logs.
        """
        return context_processor.read_run_logs(self.project, self.ENTITY_TYPE, self.id)

    def stop(self) -> None:
        """
        Stop run.
        """
        return context_processor.stop_entity(self.project, self.ENTITY_TYPE, self.id)

    def resume(self) -> None:
        """
        Resume run.
        """
        return context_processor.resume_entity(self.project, self.ENTITY_TYPE, self.id)

    ##############################
    #  Helpers
    ##############################

    def _setup_execution(self) -> None:
        """
        Setup run execution.
        """

    def start_execution(self) -> None:
        """
        Start run execution.
        """
        self._context().set_run(self)
        if self.spec.local_execution:
            # Check run state
            if self.status.state not in (State.BUILT.value, State.STOPPED.value):
                raise EntityError("Run is not in a state to run.")

            self.status.state = State.RUNNING.value
            self.save(update=True)

    def end_execution(self) -> None:
        """
        End run execution.
        """
        self._context().unset_run()

    def set_status(self, status: dict) -> None:
        """
        Set run status.

        Parameters
        ----------
        status : dict
            Status to set.
        """
        self.status: RunStatus = entity_factory.build_status(self.kind, **status)

    def _get_runtime(self) -> Runtime:
        """
        Build runtime to build run or execute it.

        Returns
        -------
        Runtime
            Runtime object.
        """
        return runtime_factory.build_runtime(self.kind, self.project)

    def _get_executable(self) -> dict:
        """
        Get executable object from backend. Reimplemented to avoid
        circular imports.

        Returns
        -------
        dict
            Executable (function or workflow) from backend.
        """
        exec_kind = entity_factory.get_executable_kind(self.kind)
        exec_type = entity_factory.get_entity_type_from_kind(exec_kind)
        string_to_split = getattr(self.spec, exec_type)
        exec_name, exec_id = string_to_split.split("://")[-1].split("/")[-1].split(":")
        return context_processor.read_context_entity(
            exec_name,
            entity_type=exec_type,
            project=self.project,
            entity_id=exec_id,
        ).to_dict()

    def _get_task(self) -> dict:
        """
        Get object from backend. Reimplemented to avoid
        circular imports.

        Returns
        -------
        dict
            Task from backend.
        """
        task_id = self.spec.task.split("://")[-1].split("/")[-1]
        return context_processor.read_unversioned_entity(
            task_id,
            entity_type=EntityTypes.TASK.value,
            project=self.project,
        ).to_dict()
