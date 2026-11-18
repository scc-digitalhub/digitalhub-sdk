# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from collections.abc import ContextManager
from typing import Protocol

from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.files import MaterialFile
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities._mixin.material.status import MaterialStatus
    from digitalhub.utils.types import SourcesOrListOfSources


class MaterialProtocol(VersionedEntityProtocol, Protocol):
    spec: MaterialSpec
    status: MaterialStatus
    extensions: list[dict]

    def as_file(self) -> ContextManager[list[str]]: ...

    def download(self, destination: str | None = None, overwrite: bool = False) -> str: ...

    def upload(self, source: SourcesOrListOfSources, keep_dir_structure: bool = False) -> None: ...

    def _update_attributes(self, obj: MaterialProtocol) -> None: ...

    @property
    def files(self) -> list[MaterialFile]: ...
