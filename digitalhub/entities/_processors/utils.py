# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import get_context
from digitalhub.entities._commons.keys import EntityKey, is_valid_key
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._mixin.executable.protocol import ExecutableProtocol


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
    key = EntityKey.parse(identifier)
    return key.project, key.entity_type, key.kind, key.name, key.id


def get_context_from_identifier(
    identifier: str,
    project: str | None = None,
) -> Context:
    if not is_valid_key(identifier):
        if project is None:
            raise EntityError("Specify project if you do not specify entity key.")
    else:
        project = EntityKey.parse(identifier).project

    return get_context(project)


def update_entity_identity(
    entity: ContextEntity | ExecutableProtocol,
    project: str,
    new_id: str | None = None,
) -> None:
    entity.project = project
    entity.metadata.project = project
    if new_id is not None:
        entity.id = new_id
        entity.metadata.version = new_id

    versioned_initializer = getattr(entity, "_init_versioned_identity", None)
    if callable(versioned_initializer):
        versioned_initializer(project, entity.name, entity.id, entity.kind)
        return

    unversioned_initializer = getattr(entity, "_init_unversioned_identity", None)
    if callable(unversioned_initializer):
        unversioned_initializer(project, entity.id, entity.kind)
        return

    raise EntityError(f"Entity '{type(entity).__name__}' has no supported identity initializer.")
