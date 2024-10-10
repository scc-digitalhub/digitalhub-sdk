from __future__ import annotations

from digitalhub.entities.run.spec import RunParams, RunSpec


class RunSpecContainer(RunSpec):
    """Run Container specification."""

    def __init__(
        self,
        task: str,
        local_execution: bool = False,
        function: str | None = None,
        node_selector: dict | None = None,
        volumes: list | None = None,
        resources: dict | None = None,
        affinity: dict | None = None,
        tolerations: list | None = None,
        envs: list | None = None,
        secrets: list | None = None,
        profile: str | None = None,
        source: dict | None = None,
        image: str | None = None,
        base_image: str | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        backoff_limit: int | None = None,
        schedule: str | None = None,
        replicas: int | None = None,
        service_ports: list | None = None,
        service_type: str | None = None,
        instructions: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            task,
            local_execution,
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
        self.source = source
        self.image = image
        self.base_image = base_image
        self.command = command
        self.args = args
        self.backoff_limit = backoff_limit
        self.schedule = schedule
        self.replicas = replicas
        self.service_ports = service_ports
        self.service_type = service_type
        self.instructions = instructions


class RunParamsContainer(RunParams):
    """Run Container parameters."""

    # Function parameters
    source: dict = None
    image: str = None
    base_image: str = None
    command: str = None
    args: list[str] = None

    # Task job
    backoff_limit: int = None
    schedule: str = None

    # Task deploy
    replicas: int = None

    # Task serve
    service_ports: list[dict] = None
    service_type: str = None

    # Task build
    instructions: list[str] = None
