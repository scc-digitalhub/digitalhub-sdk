# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.model._base.entity import Model

if typing.TYPE_CHECKING:
    from digitalhub.entities.model._tvm.spec import ModelSpecTvm
    from digitalhub.entities.model._tvm.status import ModelStatusTvm


class ModelTvm(Model):
    """
    Shared base entity for TVM models (tvm-ir / tvm-so).
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: ModelSpecTvm
        self.status: ModelStatusTvm
