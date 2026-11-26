# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.status import Status


class ContainerimageStatus(Status):
    """
    Container image status.
    """

    media_type: str | None = None
    digest: str | None = None
    size: int | None = None
    tags: list[str] | None = None
    manifest: dict | None = None
    layers: list[dict] | None = None
