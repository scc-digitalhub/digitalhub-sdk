# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations


def base_ra(entity_type: str) -> dict[str, str]:
    return {"entity_type": entity_type}


def base_entity_ra(entity_type: str, entity_name: str) -> dict[str, str]:
    return {"entity_type": entity_type, "entity_name": entity_name}


def ctx_ra(project: str) -> dict[str, str]:
    return {"project": project}


def ctx_entity_ra(project: str, entity_type: str) -> dict[str, str]:
    return {"project": project, "entity_type": entity_type}


def ctx_entity_id_ra(project: str, entity_type: str, entity_id: str) -> dict[str, str]:
    return {"project": project, "entity_type": entity_type, "entity_id": entity_id}


def ctx_metric_ra(
    project: str,
    entity_type: str,
    entity_id: str,
    metric_name: str | None,
) -> dict[str, str | None]:
    return {"project": project, "entity_type": entity_type, "entity_id": entity_id, "metric_name": metric_name}
