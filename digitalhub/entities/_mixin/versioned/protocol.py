# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import ClassVar, Protocol

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities._base.metadata.entity import Metadata


class VersionedEntityProtocol(Protocol):
    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str
    metadata: Metadata
    spec: Spec
    status: Status
    user: str | None

    def to_dict(self) -> dict: ...

    def save(self, update: bool = False): ...

    def refresh(self): ...

    def export(self) -> str: ...

    def _context(self): ...

    def _post_read_hook(self) -> None: ...

    def _post_create_hook_before_save(self) -> None: ...
