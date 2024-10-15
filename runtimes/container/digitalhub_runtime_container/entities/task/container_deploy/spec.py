from __future__ import annotations

from digitalhub.entities.task.spec import TaskSpecK8s, TaskValidatorK8s


class TaskSpecContainerDeploy(TaskSpecK8s):
    """
    TaskSpecContainerDeploy specifications.
    """

    def __init__(
        self,
        function: str,
        node_selector: dict | None = None,
        volumes: list | None = None,
        resources: dict | None = None,
        affinity: dict | None = None,
        tolerations: list | None = None,
        envs: list | None = None,
        secrets: list | None = None,
        profile: str | None = None,
        replicas: int | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            function,
            node_selector,
            volumes,
            resources,
            affinity,
            tolerations,
            envs,
            secrets,
            profile,
            **kwargs,
        )
        self.replicas = replicas


class TaskValidatorContainerDeploy(TaskValidatorK8s):
    """
    TaskValidatorContainerDeploy validator.
    """

    replicas: int = None
    """Replicas."""
