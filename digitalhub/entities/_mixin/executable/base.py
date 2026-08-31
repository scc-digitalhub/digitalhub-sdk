# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from typing import ClassVar


class ExecutableBaseMixin:
    ENTITY_TYPE: ClassVar[str]
    project: str
    kind: str
    name: str
    id: str
    key: str

    def _get_executable_string(self) -> str:
        return f"{self.kind}://{self.project}/{self.name}:{self.id}"
