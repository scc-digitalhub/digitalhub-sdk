# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from typing import ClassVar

from digitalhub.entities._commons.keys import EntityRef


class ExecutableBaseMixin:
    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str

    def _get_executable_string(self) -> str:
        return str(EntityRef(self.kind, self.project, id=self.id, name=self.name))
