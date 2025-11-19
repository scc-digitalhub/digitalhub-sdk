# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel


class Signature(BaseModel):
    """
    MLFlow model signature.
    """

    inputs: str | None = None
    outputs: str | None = None
    params: str | None = None

    def to_dict(self):
        return self.model_dump()


class Dataset(BaseModel):
    """
    MLFlow model dataset.
    """

    name: str | None = None
    digest: str | None = None
    profile: str | None = None
    dataset_schema: str | None = None
    source: str | None = None
    source_type: str | None = None

    def to_dict(self):
        return self.model_dump()
