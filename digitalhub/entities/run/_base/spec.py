# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities.task._base.models import K8s


class RunSpec(Spec, K8s):
    """RunSpec specifications."""

    function: str | None = None
    workflow: str | None = None

    task: str
    """The task string associated with the run."""


class LocalExecutionSpecMixin(Spec):
    """Spec mixin for runs that support local execution."""

    local_execution: bool = False
    """Whether to execute the run locally instead of in the cluster."""
