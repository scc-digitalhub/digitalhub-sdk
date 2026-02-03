# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities.dataitem._base.entity import Dataitem

if typing.TYPE_CHECKING:
    from digitalhub.entities.dataitem.croissant.spec import DataitemSpecCroissant
    from digitalhub.entities.dataitem.croissant.status import DataitemStatusCroissant


class DataitemCroissant(Dataitem):
    """
    DataitemCroissant class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: DataitemSpecCroissant
        self.status: DataitemStatusCroissant

    @refresh_decorator
    def as_dataset(self, **kwargs: Any) -> Any:
        raise NotImplementedError
