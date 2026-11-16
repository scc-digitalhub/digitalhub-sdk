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


class TaskSpecWorkflow(TaskSpec, K8s):
    """TaskSpecWorkflow specifications."""

    workflow: str
