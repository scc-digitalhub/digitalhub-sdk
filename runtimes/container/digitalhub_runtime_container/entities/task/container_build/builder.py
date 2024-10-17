from __future__ import annotations

from digitalhub_runtime_container.entities.task.container_build.entity import TaskContainerBuild
from digitalhub_runtime_container.entities.task.container_build.spec import (
    TaskSpecContainerBuild,
    TaskValidatorContainerBuild,
)
from digitalhub_runtime_container.entities.task.container_build.status import TaskStatusContainerBuild

from digitalhub.entities.task._base.builder import TaskBuilder


class TaskContainerBuildBuilder(TaskBuilder):
    """
    TaskContainerBuild builder.
    """

    ENTITY_CLASS = TaskContainerBuild
    ENTITY_SPEC_CLASS = TaskSpecContainerBuild
    ENTITY_SPEC_VALIDATOR = TaskValidatorContainerBuild
    ENTITY_STATUS_CLASS = TaskStatusContainerBuild
    ENTITY_KIND = "container+build"
    ACTION = "build"
