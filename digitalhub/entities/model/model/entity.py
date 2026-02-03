# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.model._base.entity import Model

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.model.spec import ModelSpecModel
    from digitalhub.entities.model.model.status import ModelStatusModel


class ModelModel(Model):
    """
    ModelModel class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: ModelSpecModel
        self.status: ModelStatusModel
