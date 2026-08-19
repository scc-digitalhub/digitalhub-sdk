# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import ClassVar

from digitalhub.entities._processors.processors import key_processor


class UnversionedMixin:
    """Mixin for entities whose name is derived from the identifier."""

    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str

    def _init_unversioned_identity(self, project: str, uuid: str, kind: str) -> None:
        self.id = uuid
        self.name = uuid
        self.key = key_processor.build_context_entity_key(
            project,
            self.ENTITY_TYPE,
            kind,
            uuid,
        )
