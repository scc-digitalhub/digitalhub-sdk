# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities.model._tvm.entity import ModelTvm

if typing.TYPE_CHECKING:
    from digitalhub.entities.model.tvm_so.spec import ModelSpecTvmSo


class ModelTvmSo(ModelTvm):
    """
    ModelTvmSo class.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.spec: ModelSpecTvmSo
