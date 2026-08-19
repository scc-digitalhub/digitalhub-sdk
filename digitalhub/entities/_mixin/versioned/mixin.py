# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar

from digitalhub.entities._processors.processors import key_processor


class VersionedMixin:
    """Mixin for entities with a separate name and versioned identity."""

    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str

    def _init_versioned_identity(self, project: str, name: str, uuid: str, kind: str) -> None:
        self.name = name
        self.id = uuid
        self.key = key_processor.build_context_entity_key(
            project,
            self.ENTITY_TYPE,
            kind,
            name,
            uuid,
        )
