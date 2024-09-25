from __future__ import annotations

from digitalhub_data.entities.run.spec import RunParamsData, RunSpecData


class RunSpecKFP(RunSpecData):
    """Run KFP Pipline specification."""

    def __init__(
        self,
        task: str,
        local_execution: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(task, local_execution)

        self.source = kwargs.get("source")
        self.image = kwargs.get("image")
        self.tag = kwargs.get("tag")
        self.handler = kwargs.get("handler")

        self.function = kwargs.get("function")
        self.node_selector = kwargs.get("node_selector")
        self.volumes = kwargs.get("volumes")
        self.resources = kwargs.get("resources")
        self.affinity = kwargs.get("affinity")
        self.tolerations = kwargs.get("tolerations")
        self.env = kwargs.get("env")
        self.secrets = kwargs.get("secrets")
        self.profile = kwargs.get("profile")

        self.schedule = kwargs.get("schedule")
        self.replicas = kwargs.get("replicas")

        self.inputs = kwargs.get("inputs")
        self.outputs = kwargs.get("outputs")
        self.parameters = kwargs.get("parameters")
        self.values = kwargs.get("values")


class RunParamsKFP(RunParamsData):
    """Run KFP parameters."""

    # Workflow parameters
    source: dict = None
    image: str = None
    tag: str = None
    handler: str = None

    # Task parameters
    function: str = None
    node_selector: list[dict] = None
    volumes: list[dict] = None
    resources: dict = None
    affinity: dict = None
    tolerations: list[dict] = None
    env: list[dict] = None
    secrets: list[str] = None
    profile: str = None

    # Pipeline parameters
    schedule: str = None

    # Run parameters
    inputs: dict = None
    outputs: dict = None
    parameters: dict = None
    values: list = None
