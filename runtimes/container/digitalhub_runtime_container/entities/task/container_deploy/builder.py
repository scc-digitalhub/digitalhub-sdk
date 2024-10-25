from __future__ import annotations

from digitalhub_runtime_container.entities._base.runtime_entity.builder import RuntimeEntityBuilderContainer
from digitalhub_runtime_container.entities.task.container_deploy.entity import TaskContainerDeploy
from digitalhub_runtime_container.entities.task.container_deploy.spec import (
    TaskSpecContainerDeploy,
    TaskValidatorContainerDeploy,
)
from digitalhub_runtime_container.entities.task.container_deploy.status import TaskStatusContainerDeploy

from digitalhub.entities.task._base.builder import TaskBuilder


class TaskContainerDeployBuilder(TaskBuilder, RuntimeEntityBuilderContainer):
    """
    TaskContainerDeployBuilder deployer.
    """

    ENTITY_CLASS = TaskContainerDeploy
    ENTITY_SPEC_CLASS = TaskSpecContainerDeploy
    ENTITY_SPEC_VALIDATOR = TaskValidatorContainerDeploy
    ENTITY_STATUS_CLASS = TaskStatusContainerDeploy
    ENTITY_KIND = "container+deploy"