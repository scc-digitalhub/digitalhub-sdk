from __future__ import annotations

from digitalhub.entities.run.spec import RunParams, RunSpec


class RunSpecModelserve(RunSpec):
    """Run model serving specification."""

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
        image: str | None = None,
        path: str | None = None,
        model_name: str | None = None,
        model_key: str | None = None,
        service_type: str | None = None,
        replicas: int | None = None,
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
        self.image = image
        self.path = path
        self.model_name = model_name
        self.model_key = model_key
        self.service_type = service_type
        self.replicas = replicas


class RunParamsModelserve(RunParams):
    """Run Model serving parameters."""

    # Function parameters
    image: str = None
    path: str = None
    model_name: str = None
    model_key: str = None

    # Task serve
    service_type: str = None
    replicas: int = None


class RunSpecSklearnserve(RunSpecModelserve):
    """Run SKLearn model serving specification."""


class RunSpecMlflowserve(RunSpecModelserve):
    """Run MLFLow model serving specification."""


class RunSpecHuggingfaceserve(RunSpecModelserve):
    """Run Huggingface model serving specification."""


class RunParamsSklearnserve(RunParamsModelserve):
    """Run SKLearn model serving parameters."""


class RunParamsMlflowserve(RunParamsModelserve):
    """Run MLFLow model serving parameters."""


class RunParamsHuggingfaceserve(RunParamsModelserve):
    """Run Huggingface model serving parameters."""
