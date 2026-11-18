# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


def build_project_key(project: str) -> str:
    """Build the canonical key for a project."""
    return f"store://{project}"


def build_context_entity_key(
    project: str,
    entity_type: str,
    entity_kind: str,
    entity_name: str,
    entity_id: str | None = None,
) -> str:
    """Build the canonical key for a context entity."""
    key = f"store://{project}/{entity_type}/{entity_kind}/{entity_name}"
    return f"{key}:{entity_id}" if entity_id is not None else key
