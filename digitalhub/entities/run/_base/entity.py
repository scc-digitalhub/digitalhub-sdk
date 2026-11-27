# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.extensions.mixin import ExtensionsMixin
from digitalhub.entities._mixin.metrics.mixin import MetricsMixin
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin
from digitalhub.entities._processors.context.control import ContextEntityControlProcessor
from digitalhub.entities.run._base.processor import RunProcessor
from digitalhub.entities.run._base.serve_processor import RunServeProcessor
from digitalhub.factory.entity import entity_factory

if typing.TYPE_CHECKING:
    from requests import Response

    from digitalhub.entities._base.metadata.entity import Metadata
    from digitalhub.entities.log._base.entity import Log
    from digitalhub.entities.run._base.serve_processor import ServeRun
    from digitalhub.entities.run._base.spec import LocalExecutionSpecMixin, RunSpec
    from digitalhub.entities.run._base.status import RunStatus


class LocalExecutionRunMixin:
    """Entity mixin for runs that support local execution."""

    spec: LocalExecutionSpecMixin

    def local_execution(self) -> bool:
        """Return whether this run is configured for local execution."""
        return self.spec.local_execution


class ServeRunMixin:
    """Entity mixin for serve runs, whose service can be invoked."""

    # Service url and whether it answered without the proxy: probed once.
    _direct_service: tuple[str, bool] | None = None

    def invoke(self, method: str | None = None, path: str | None = None, **kwargs) -> Response:
        """
        Call the service of the run.

        The service is called directly when it answers, for example from
        inside the cluster; otherwise through the proxy in front of the
        cluster, configured with ``DHCORE_PROXY``, with the credentials of
        the SDK. The first call finds out which, and the run remembers it.

        Parameters
        ----------
        method : str | None
            HTTP method. Defaults to POST when ``data`` or ``json`` is given,
            otherwise to GET.
        path : str | None
            Path on the service, for example ``/v2/models/model/infer``.
            Defaults to the root of the service.
        **kwargs : dict
            Keyword arguments of ``requests.request()``.

        Returns
        -------
        Response
            Response of the service.
        """
        return RunServeProcessor().invoke(typing.cast("ServeRun", self), method, path, **kwargs)


class Run(ContextEntity, UnversionedMixin, MetricsMixin, ExtensionsMixin):
    """
    A class representing a run.
    """

    ENTITY_TYPE = EntityTypes.RUN.value
    _obj_attr = (*ContextEntity._obj_attr, *ExtensionsMixin._obj_attr)

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: RunSpec,
        status: RunStatus,
        extensions: list[dict] | None = None,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_unversioned_identity(project, uuid, kind)

        self.spec: RunSpec
        self.status: RunStatus

        self.name = name
        self._init_metrics_state()

        self._init_extensions(extensions)

    ##############################
    #  Run Methods
    ##############################

    def build(self) -> None:
        """
        Build run.
        """
        RunProcessor().build(self)

    def run(self) -> Run:
        """
        Run run.

        Returns
        -------
        Run
            Run object.
        """
        return RunProcessor().run(self)

    def wait(
        self,
        log_info: bool = True,
        timeout: float | None = None,
        poll_interval: float = 5.0,
    ) -> Run:
        """
        Wait for run to finish.

        Parameters
        ----------
        log_info : bool
            If True, log information.
        timeout : float | None
            Maximum time to wait in seconds. If None, wait indefinitely.
        poll_interval : float
            Time to wait between status checks in seconds.

        Returns
        -------
        Run
            Run object.
        """
        return RunProcessor().wait(
            self,
            log_info=log_info,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    def logs(self, as_entity: bool = False) -> list[Log] | list[str]:
        """
        Get run logs. If no logs are present, an empty list is returned.
        In case of local execution, logs are printed to console.

        Returns
        -------
        list[Log] | list[str]
            List of run logs. If `as_entity` is True, returns a list of `Log` objects, otherwise returns a list of log texts.
        """
        return RunProcessor().read_logs(self, as_entity=as_entity)

    def stop(self) -> None:
        """
        Stop run.
        """
        return ContextEntityControlProcessor().stop_entity(self.project, self.ENTITY_TYPE, self.id)

    def resume(self) -> None:
        """
        Resume run.
        """
        return ContextEntityControlProcessor().resume_entity(self.project, self.ENTITY_TYPE, self.id)

    ##############################
    #  Helpers
    ##############################

    def local_execution(self) -> bool:
        """
        Check if run has local execution. By defautlt is False, but it can
        be overridden by specific runtimes that support local execution.

        Returns
        -------
        bool
            True if run has local execution, False otherwise.
        """
        return False

    def _setup_execution(self) -> None:
        """
        Setup run execution.
        """

    def start_execution(self) -> None:
        """
        Start run execution.
        """
        RunProcessor().start_execution(self)

    def end_execution(self) -> None:
        """
        End run execution.
        """
        RunProcessor().end_execution(self)

    def set_status(self, status: dict) -> None:
        """
        Set run status.

        Parameters
        ----------
        status : dict
            Status to set.
        """
        self.status = entity_factory.build_status(self.kind, **status)
