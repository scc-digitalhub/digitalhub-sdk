# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities._frameworks.k8s.models import K8s
from digitalhub.entities._mixin.execution.spec import (
    BuildSpecMixin,
    FunctionSpecMixin,
    ServeSpecMixin,
    WorkflowSpecMixin,
)

__all__ = [
    "BuildSpecMixin",
    "ServeSpecMixin",
    "TaskSpecFunction",
    "TaskSpecWorkflow",
]


class TaskSpecFunction(FunctionSpecMixin, Spec, K8s):
    """TaskSpecFunction specifications."""


class TaskSpecWorkflow(WorkflowSpecMixin, Spec, K8s):
    """TaskSpecWorkflow specifications."""
