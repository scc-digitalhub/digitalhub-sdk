# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from digitalhub.entities.artifact._base.entity import Artifact
    from digitalhub.entities.dataitem._base.entity import Dataitem
    from digitalhub.entities.function._base.entity import Function
    from digitalhub.entities.model._base.entity import Model
    from digitalhub.entities.workflow._base.entity import Workflow


class ProjectListShortcuts(typing.Protocol):
    """Static declarations for dynamically bound project list shortcuts."""

    def list_functions(self, *args, **kwargs) -> list[Function]: ...

    def list_workflows(self, *args, **kwargs) -> list[Workflow]: ...

    def list_artifacts(self, *args, **kwargs) -> list[Artifact]: ...

    def list_dataitems(self, *args, **kwargs) -> list[Dataitem]: ...

    def list_models(self, *args, **kwargs) -> list[Model]: ...
