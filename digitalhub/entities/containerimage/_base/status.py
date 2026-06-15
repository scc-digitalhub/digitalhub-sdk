# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.status import Status


class ContainerimageStatus(Status):
    """
    ImageStatus status.
    """

    def __init__(
        self,
        state: str | None = None,
        message: str | None = None,
        transitions: list[dict] | None = None,
        k8s: dict[str, object] | None = None,
        media_type: str | None = None,
        digest: str | None = None,
        size: int | None = None,
        tags: list[str] | None = None,
        manifest: dict | None = None,
        layers: list[dict] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(state, message, transitions, k8s, **kwargs)
        self.media_type = media_type
        self.digest = digest
        self.size = size
        self.tags = tags
        self.manifest = manifest
        self.layers = layers
