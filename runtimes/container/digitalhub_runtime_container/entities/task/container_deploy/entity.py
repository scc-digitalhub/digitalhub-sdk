from __future__ import annotations

import typing

from digitalhub.entities.task._base.entity import Task

if typing.TYPE_CHECKING:
    from digitalhub_runtime_container.entities.task.container_deploy.spec import TaskSpecContainerDeploy
    from digitalhub_runtime_container.entities.task.container_deploy.status import TaskStatusContainerDeploy

    from digitalhub.entities._base.entity.metadata import Metadata


class TaskContainerDeploy(Task):
    """
    TaskContainerDeploy class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TaskSpecContainerDeploy,
        status: TaskStatusContainerDeploy,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: TaskSpecContainerDeploy
        self.status: TaskStatusContainerDeploy
