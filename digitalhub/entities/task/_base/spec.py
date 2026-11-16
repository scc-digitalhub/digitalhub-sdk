# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities.task._base.models import K8s


class TaskSpec(Spec):
    """TaskSpec specifications."""


class TaskSpecFunction(TaskSpec, K8s):
    """TaskSpecFunction specifications."""

    function: str


class BuildSpecMixin(Spec):
    """Spec mixin for build action fields."""

    instructions: list[str] | None = None


class WorkflowSpecMixin(Spec):
    """Spec mixin for workflow task and run fields."""

    workflow: str


class TaskSpecWorkflow(WorkflowSpecMixin, TaskSpec, K8s):
    """TaskSpecWorkflow specifications."""
