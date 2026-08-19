# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


class ContextEntityKeyProcessor:
    def build_context_entity_key(
        self,
        project: str,
        entity_type: str,
        entity_kind: str,
        entity_name: str,
        entity_id: str | None = None,
    ) -> str:
        if entity_id is None:
            return f"store://{project}/{entity_type}/{entity_kind}/{entity_name}"
        return f"store://{project}/{entity_type}/{entity_kind}/{entity_name}:{entity_id}"
