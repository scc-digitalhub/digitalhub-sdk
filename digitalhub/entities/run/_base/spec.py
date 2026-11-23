# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities._frameworks.k8s.models import K8s
from digitalhub.entities._mixin.execution.spec import FunctionSpecMixin, WorkflowSpecMixin


class RunSpec(Spec, K8s):
    """Common Run specification."""

    task: str
    """The task string associated with the run."""


class RunSpecFunction(FunctionSpecMixin, RunSpec):
    """Run specification linked to a Function."""


class RunSpecWorkflow(WorkflowSpecMixin, RunSpec):
    """Run specification linked to a Workflow."""


class LocalExecutionSpecMixin(Spec):
    """Spec mixin for runs that support local execution."""

    local_execution: bool = False
    """Whether to execute the run locally instead of in the cluster."""
