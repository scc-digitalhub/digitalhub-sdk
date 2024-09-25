from __future__ import annotations

from digitalhub_core.entities.task.spec import TaskParamsK8s, TaskSpecK8s


class TaskSpecPipeline(TaskSpecK8s):
    """Task Pipeline specification."""

    def __init__(
        self,
        function: str,
        schedule: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(function, **kwargs)
        self.schedule = schedule


class TaskParamsPipeline(TaskParamsK8s):
    """
    TaskParamsPipeline model.
    """

    schedule: str = None
    """KFP schedule specification."""


class TaskSpecBuild(TaskSpecK8s):
    """Task Build specification."""

    def __init__(
        self,
        function: str,
        **kwargs,
    ) -> None:
        super().__init__(function, **kwargs)


class TaskParamsBuild(TaskParamsK8s):
    pass
