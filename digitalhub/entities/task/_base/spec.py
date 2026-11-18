# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities.task._base.models import CorePort, CoreServiceType, K8s


class TaskSpecFunction(Spec, K8s):
    """TaskSpecFunction specifications."""

    function: str


class BuildSpecMixin(Spec):
    """Spec mixin for build action fields."""

    instructions: list[str] | None = None


class ServeSpecMixin(Spec):
    """Common specification fields for serve actions."""

    replicas: int | None = Field(default=None, ge=0)
    service_type: CoreServiceType | None = None
    service_name: str | None = None
    service_ports: list[CorePort] | None = None


class WorkflowSpecMixin(Spec):
    """Spec mixin for workflow task and run fields."""

    workflow: str


class TaskSpecWorkflow(WorkflowSpecMixin, Spec, K8s):
    """TaskSpecWorkflow specifications."""
