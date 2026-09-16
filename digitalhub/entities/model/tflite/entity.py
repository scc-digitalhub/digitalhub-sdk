# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.model._base.entity import Model

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.tflite.spec import ModelSpecTflite
    from digitalhub.entities.model.tflite.status import ModelStatusTflite


class ModelTflite(Model):
    """
    ModelTflite class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: ModelSpecTflite
        self.status: ModelStatusTflite
