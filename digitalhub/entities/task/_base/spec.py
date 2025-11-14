# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator
from digitalhub.entities.task._base.models import K8s


class TaskSpec(Spec):
    """TaskSpec specifications."""


class TaskSpecFunction(TaskSpec):
    """TaskSpecFunction specifications."""

    def __init__(
        self,
        function: str,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        **kwargs,
    ) -> None:
        self.function = function
        self.volumes = volumes
        self.resources = resources
        self.envs = envs
        self.secrets = secrets
        self.profile = profile


class TaskSpecWorkflow(TaskSpec):
    """TaskSpecWorkflow specifications."""

    def __init__(
        self,
        workflow: str,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        **kwargs,
    ) -> None:
        self.workflow = workflow
        self.volumes = volumes
        self.resources = resources
        self.envs = envs
        self.secrets = secrets
        self.profile = profile


class TaskValidator(SpecValidator):
    """
    TaskValidator validator.
    """


class TaskValidatorFunction(TaskValidator, K8s):
    """
    TaskValidatorFunction validator.
    """

    function: str


class TaskValidatorWorkflow(TaskValidator, K8s):
    """
    TaskValidatorWorkflow validator.
    """

    workflow: str
