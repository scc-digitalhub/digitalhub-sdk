from __future__ import annotations

import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from digitalhub.entities.project._base.entity import Project


class Context:
    """
    Context class built forom a `Project` instance. It contains
    some information about the project, such as the project name,
    a client instance (local or non-local), the local context
    project path and information about client locality.
    """

    def __init__(self, project: Project) -> None:
        self.name = project.name
        self.client = project._client
        self.local = project._client.is_local()
        self.root = Path(project.spec.context)
        self.root.mkdir(parents=True, exist_ok=True)
