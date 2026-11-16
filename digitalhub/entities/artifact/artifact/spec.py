# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.artifact._base.spec import ArtifactSpec


class ArtifactSpecArtifact(ArtifactSpec):
    """
    ArtifactSpecArtifact specifications.
    """

    src_path: str | None = None
    """Source path of the artifact."""
