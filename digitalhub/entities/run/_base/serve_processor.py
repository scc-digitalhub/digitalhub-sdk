# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol

import requests

from digitalhub.entities._commons.keys import EntityRef
from digitalhub.entities._mixin.executable.enums import ExecutableActions
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.utils import get_context
from digitalhub.entities.run._base.polling import finished, wait_until
from digitalhub.factory.entity import entity_factory
from digitalhub.utils.exceptions import BuilderError, EntityError

if typing.TYPE_CHECKING:
    from requests import Response

    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.run._base.status import RunStatus

# Seconds the OPTIONS request of invoke() waits for the service before
# falling back to the proxy.
SERVICE_PROBE_TIMEOUT = 5


class ServeRun(Protocol):
    """What the serve processor needs from a run with ``ServeRunMixin``."""

    id: str
    project: str
    status: RunStatus
    _direct_service: tuple[str, bool] | None


def _service(run: Run | ServeRun) -> dict | None:
    """Service that Core publishes in the status of a serve run."""
    # Declared by the status of most serve runs; the others keep it as an extra field.
    return getattr(run.status, "service", None)


def _deployed(run: Run) -> str | None:
    """Outcome of a serve run whose service is published, or whose deployment ended."""
    return "service deployed" if _service(run) is not None else finished(run)


class RunServeProcessor:
    """Serve runs: wait for their service and invoke it."""

    def __init__(self, crud_processor: ContextEntityCRUDProcessor | None = None) -> None:
        self.crud_processor = ContextEntityCRUDProcessor() if crud_processor is None else crud_processor

    @staticmethod
    def is_serve(run: Run) -> bool:
        """Whether the run executes the serve action."""
        try:
            action = entity_factory.get_action_from_task_kind(run.kind, EntityRef.parse(run.spec.task).kind)
        except BuilderError:
            # The runtime of the run is not installed: its actions are unknown.
            return False
        return action == ExecutableActions.SERVE.value

    def wait(
        self,
        run: Run,
        log_info: bool = True,
        timeout: float | None = None,
        poll_interval: float = 5.0,
    ) -> Run:
        """
        Wait until Core publishes the service of the run, or until the run
        reaches a terminal state, for example when the deployment fails.
        """
        return wait_until(
            self.crud_processor,
            run,
            _deployed,
            "deploy its service",
            log_info=log_info,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    def invoke(self, run: ServeRun, method: str | None = None, path: str | None = None, **kwargs) -> Response:
        """
        Call the service of a serve run.

        The service is called directly when it answers an OPTIONS request, for
        example from inside the cluster; otherwise through the proxy in front
        of the cluster (``DHCORE_PROXY``).
        """
        host = (_service(run) or {}).get("url")
        if host is None:
            raise EntityError(
                f"Run {run.id} has no service url. If the service is deploying, use run.wait() or try again later."
            )
        path = "/" + path.lstrip("/") if path else ""
        if method is None:
            method = "POST" if "data" in kwargs or "json" in kwargs else "GET"
        url = f"http://{host}{path}"
        if self._answers_directly(run, host, url):
            return requests.request(method, url, **kwargs)
        return get_context(run.project).client.proxy_request(host, method, path, **kwargs)

    @staticmethod
    def _answers_directly(run: ServeRun, host: str, url: str) -> bool:
        """
        Whether the service answers without the proxy.

        The answer depends on where the SDK runs, not on the request: the run
        remembers it for its service, so only the first call waits for the
        probe.
        """
        if run._direct_service is not None and run._direct_service[0] == host:
            return run._direct_service[1]
        try:
            requests.options(url, timeout=SERVICE_PROBE_TIMEOUT)
            direct = True
        except requests.RequestException:
            direct = False
        run._direct_service = (host, direct)
        return direct
