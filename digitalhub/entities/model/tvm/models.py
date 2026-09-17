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
    """Tensor dtype (e.g. 'float32', or 'int8'/'uint8' when quantized)."""

    shape: list[int] | None = None
    """Tensor shape (e.g. [1, 3, 640, 640]); -1 marks a symbolic dim."""

    scale: list[float] | None = None
    """Affine quantization scale(s): real = (q - zero_point) * scale. Present only for
    quantized tensors, whatever the source format: a QDQ ONNX carries them exactly like
    a TFLite full-integer model."""

    zero_point: list[int] | None = None
    """Affine quantization zero point(s)."""

    quantized_dimension: int | None = None
    """Axis the per-axis scales are indexed by; absent for per-tensor quantization."""

    def to_dict(self):
        return self.model_dump()
