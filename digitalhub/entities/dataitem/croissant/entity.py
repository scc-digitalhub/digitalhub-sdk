# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._base.material.utils import refresh_decorator
from digitalhub.entities.dataitem._base.entity import Dataitem

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities._base.extensions.entity import Extension
    from digitalhub.entities.dataitem.croissant.spec import DataitemSpecCroissant
    from digitalhub.entities.dataitem.croissant.status import DataitemStatusCroissant


class DataitemCroissant(Dataitem):
    """
    DataitemCroissant class.
    """

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: DataitemSpecCroissant,
        status: DataitemStatusCroissant,
        extensions: list[Extension],
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, extensions, user)

        self.spec: DataitemSpecCroissant
        self.status: DataitemStatusCroissant

        self._query: str | None = None

    @refresh_decorator
    def as_dataset(self, **kwargs: Any) -> Any:
        raise NotImplementedError
