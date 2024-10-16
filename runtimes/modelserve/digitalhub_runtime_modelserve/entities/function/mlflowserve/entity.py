from __future__ import annotations

import typing

from digitalhub.entities.function._base.entity import Function

if typing.TYPE_CHECKING:
    from digitalhub_runtime_modelserve.entities.function.mlflowserve.spec import FunctionSpecMlflowserve
    from digitalhub_runtime_modelserve.entities.function.mlflowserve.status import FunctionStatusMlflowserve

    from digitalhub.entities._base.entity.metadata import Metadata


class FunctionMlflowserve(Function):
    """
    FunctionMlflowserve class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: FunctionSpecMlflowserve,
        status: FunctionStatusMlflowserve,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)

        self.spec: FunctionSpecMlflowserve
        self.status: FunctionStatusMlflowserve
