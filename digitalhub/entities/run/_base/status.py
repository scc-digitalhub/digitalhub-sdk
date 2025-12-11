# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.status import Status
from digitalhub.entities._base.metrics.status import MetricsStatus


class RunStatus(MetricsStatus, Status):
    """
    RunStatus status.
    """

    def __init__(
        self,
        state: str,
        message: str | None = None,
        transitions: list[dict] | None = None,
        k8s: dict | None = None,
        metrics: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            state=state,
            message=message,
            transitions=transitions,
            k8s=k8s,
            metrics=metrics,
            **kwargs,
        )
