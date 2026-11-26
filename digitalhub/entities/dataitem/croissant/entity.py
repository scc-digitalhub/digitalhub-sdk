# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Any

from digitalhub.entities._commons.utils import refresh_decorator
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.dataitem.croissant.processor import DataitemCroissantProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities._mixin.material.spec import MaterialSpec
    from digitalhub.entities.dataitem._base.status import DataitemStatus


class DataitemCroissant(Dataitem):
    """
    DataitemCroissant class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: MaterialSpec
        self.status: DataitemStatus

    @refresh_decorator
    def as_dataset(self, overwrite: bool = False) -> Any:
        """
        Get the Croissant Dataset object from the Dataitem.

        Parameters
        ----------
        overwrite : bool
            Flag to indicate overwrite of local files.

        Returns
        -------
        mlcroissant.Dataset
            Croissant Dataset object.
        """
        return DataitemCroissantProcessor().as_dataset(self, overwrite=overwrite)
