# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pydantic import BaseModel


class ProfileConfig(BaseModel):
    """
    Configuration profiles.
    """

    default_files_store: str | None = None

    def to_dict(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)
