# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import get_context
from digitalhub.entities._commons.utils import get_project_from_key, is_valid_key, parse_entity_key
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context


def parse_identifier(
    identifier: str,
    project: str | None = None,
    entity_type: str | None = None,
    entity_kind: str | None = None,
    entity_id: str | None = None,
) -> tuple[str, str, str | None, str | None, str | None]:
    if not is_valid_key(identifier):
        if project is None or entity_type is None:
            raise ValueError("Project and entity type must be specified.")
        return project, entity_type, entity_kind, identifier, entity_id
    return parse_entity_key(identifier)


def get_context_from_identifier(
    identifier: str,
    project: str | None = None,
) -> Context:
    if not is_valid_key(identifier):
        if project is None:
            raise EntityError("Specify project if you do not specify entity key.")
    else:
        project = get_project_from_key(identifier)

    return get_context(project)
