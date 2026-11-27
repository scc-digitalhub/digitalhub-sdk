# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.extensions.mixin import ExtensionsMixin
from digitalhub.entities._mixin.metrics.mixin import MetricsMixin
from digitalhub.entities._mixin.unversioned.mixin import UnversionedMixin
from digitalhub.entities._processors.context.control import ContextEntityControlProcessor
from digitalhub.entities.run._base.io_processor import RunIOProcessor
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


class BuildRunMixin:
    """Entity mixin for build runs, whose status holds the image they built."""

    @property
    def image(self) -> str | None:
        """
        Get the image built by the run.

        Returns
        -------
        str | None
            The image, or None until the build publishes it.
        """
        # Declared by the status of the build runs.
        outputs = getattr(typing.cast("Run", self).status, "outputs", None) or {}
        return outputs.get("image")


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


class EntityIORunMixin:
    """Entity mixin for runs whose inputs and outputs are entities, referenced by key."""

    def inputs(self, as_dict: bool = False) -> dict:
        """
        Get the run inputs, by parameter.

        Parameters
        ----------
        as_dict : bool
            If True, return inputs as dictionaries.

        Returns
        -------
        dict
            Input entities, or their dictionaries.
        """
        return RunIOProcessor().inputs(typing.cast("Run", self), as_dict=as_dict)

    def output(
        self,
        output_name: str,
        as_key: bool = False,
        as_dict: bool = False,
    ) -> ContextEntity | dict | str | None:
        """
        Get a run output by name.

        Parameters
        ----------
        output_name : str
            Name of the output.
        as_key : bool
            If True, return the key of the output.
        as_dict : bool
            If True, return the output as a dictionary.

        Returns
        -------
        ContextEntity | dict | str | None
            Output entity, its dictionary or its key; None if the run has no
            output with that name.
        """
        return RunIOProcessor().output(typing.cast("Run", self), output_name, as_key=as_key, as_dict=as_dict)

    def outputs(self, as_key: bool = False, as_dict: bool = False) -> dict:
        """
        Get the run outputs, by name.

        Parameters
        ----------
        as_key : bool
            If True, return the keys of the outputs.
        as_dict : bool
            If True, return outputs as dictionaries.

        Returns
        -------
        dict
            Output entities, their dictionaries or their keys.
        """
        return RunIOProcessor().outputs(typing.cast("Run", self), as_key=as_key, as_dict=as_dict)

    def _setup_execution(self) -> None:
        """
        Prepare the inputs before the execution.
        """
        RunIOProcessor().prepare_inputs(typing.cast("Run", self))


class ResultsRunMixin:
    """Entity mixin for runs whose status holds result values."""

    def result(self, result_name: str) -> Any:
        """
        Get a result by name.

        Parameters
        ----------
        result_name : str
            Name of the result.

        Returns
        -------
        Any
            The result, or None.
        """
        return self.results().get(result_name)

    def results(self) -> dict:
        """
        Get the results.

        Returns
        -------
        dict
            The results, by name.
        """
        # Declared by the status of the runs that publish results.
        return getattr(typing.cast("Run", self).status, "results", None) or {}


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
