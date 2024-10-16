from __future__ import annotations

import typing

from digitalhub.entities.task._base.entity import Task

if typing.TYPE_CHECKING:
    from digitalhub_runtime_python.entities.task.python_build.spec import TaskSpecPythonBuild
    from digitalhub_runtime_python.entities.task.python_build.status import TaskStatusPythonBuild

    from digitalhub.entities._base.entity.metadata import Metadata


class TaskPythonBuild(Task):
    """
    TaskPythonBuild class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: TaskSpecPythonBuild,
        status: TaskStatusPythonBuild,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: TaskSpecPythonBuild
        self.status: TaskStatusPythonBuild
