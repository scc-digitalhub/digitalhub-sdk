# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel


class TensorSpec(BaseModel):
    """
    TVM model tensor (input/output) signature.
    """

    name: str | None = None
    """Tensor name."""

    dtype: str | None = None
    """Tensor dtype (e.g. 'float32')."""

    shape: list[int] | None = None
    """Tensor shape (e.g. [1, 3, 640, 640]); -1 marks a symbolic dim."""

    def to_dict(self):
        return self.model_dump()
