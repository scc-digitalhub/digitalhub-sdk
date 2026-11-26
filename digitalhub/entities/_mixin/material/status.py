# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.status import Status


class MaterialStatus(Status):
    """
    Status of material entities, with the files they hold.
    """

    files: list[dict] | None = None
