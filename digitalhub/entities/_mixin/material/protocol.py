# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol

from digitalhub.entities._mixin.versioned.protocol import VersionedEntityProtocol

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities._mixin.material.status import MaterialStatus
    from digitalhub.utils.types import SourcesOrListOfSources


class MaterialEntityProtocol(VersionedEntityProtocol, Protocol):
    spec: MaterialSpec
    status: MaterialStatus
    extensions: list[dict]

    def as_file(self) -> list[str]: ...

    def download(self, destination: str | None = None, overwrite: bool = False) -> str: ...

    def upload(self, source: SourcesOrListOfSources, keep_dir_structure: bool = False) -> None: ...

    @property
    def files(self) -> list[dict]: ...
