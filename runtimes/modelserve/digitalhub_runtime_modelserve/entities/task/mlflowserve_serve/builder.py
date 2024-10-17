from __future__ import annotations

from digitalhub_runtime_modelserve.entities.task.mlflowserve_serve.entity import TaskMlflowserveServe
from digitalhub_runtime_modelserve.entities.task.mlflowserve_serve.spec import (
    TaskSpecMlflowserveServe,
    TaskValidatorMlflowserveServe,
)
from digitalhub_runtime_modelserve.entities.task.mlflowserve_serve.status import TaskStatusMlflowserveServe

from digitalhub.entities.task._base.builder import TaskBuilder


class TaskMlflowserveServeBuilder(TaskBuilder):
    """
    TaskMlflowserveServe builder.
    """

    ENTITY_CLASS = TaskMlflowserveServe
    ENTITY_SPEC_CLASS = TaskSpecMlflowserveServe
    ENTITY_SPEC_VALIDATOR = TaskValidatorMlflowserveServe
    ENTITY_STATUS_CLASS = TaskStatusMlflowserveServe
    ENTITY_KIND = "mlflowserve+serve"
    ACTION = "serve"
