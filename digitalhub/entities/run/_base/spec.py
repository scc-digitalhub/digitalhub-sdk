from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator
from digitalhub.entities.task._base.models import K8s


class RunSpec(Spec):
    """RunSpec specifications."""

    def __init__(
        self,
        task: str,
        local_execution: bool = False,
        function: str | None = None,
        workflow: str | None = None,
        node_selector: list[dict] | None = None,
        volumes: list[dict] | None = None,
        resources: dict | None = None,
        affinity: dict | None = None,
        tolerations: list[dict] | None = None,
        envs: list[dict] | None = None,
        secrets: list[str] | None = None,
        profile: str | None = None,
        **kwargs,
    ) -> None:
        self.task = task
        self.local_execution = local_execution
        self.function = function
        self.workflow = workflow
        self.node_selector = node_selector
        self.volumes = volumes
        self.resources = resources
        self.affinity = affinity
        self.tolerations = tolerations
        self.envs = envs
        self.secrets = secrets
        self.profile = profile


class RunValidator(SpecValidator, K8s):
    """
    RunValidator validator.
    """

    # Task parameters
    function: str = None
    workflow: str = None

    # Run parameters
    task: str
    """The task string associated with the run."""

    local_execution: bool = False
    """Flag to indicate if the run will be executed locally."""
