# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import Field

from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities._frameworks.k8s.models import CorePort, CoreServiceType


class FunctionSpecMixin(Spec):
    """Fields shared by Task and Run specs linked to a Function."""

    function: str


class WorkflowSpecMixin(Spec):
    """Fields shared by Task and Run specs linked to a Workflow."""

    workflow: str


class BuildSpecMixin(Spec):
    """Spec mixin for build action fields."""

    instructions: list[str] | None = None


class ServeSpecMixin(Spec):
    """Common specification fields for serve actions."""

    replicas: int | None = Field(default=None, ge=0)
    service_type: CoreServiceType | None = None
    service_name: str | None = None
    service_ports: list[CorePort] | None = None
