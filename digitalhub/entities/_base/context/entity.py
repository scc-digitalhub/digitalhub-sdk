# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.context.api import get_context
from digitalhub.entities._base.entity.entity import PersistedEntity
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor

if typing.TYPE_CHECKING:
    from digitalhub.context.context import Context
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities._base.metadata.entity import Metadata


class ContextEntity(PersistedEntity):
    """Active Record facade for entities persisted in a project context.

    Identity, spec, and status stay on the entity. Backend persistence and
    context lookup are delegated through the explicit SDK processors.
    """

    _obj_attr = (*PersistedEntity._obj_attr, "project", "id", "name")

    def __init__(
        self,
        project: str,
        kind: str,
        metadata: Metadata,
        spec: Spec,
        status: Status,
        user: str | None = None,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)
        self.project = project
        self.name: str
        self.id: str

    ##############################
    #  Active Record persistence
    ##############################

    def save(self, update: bool = False) -> ContextEntity:
        """
        Save the entity into the backend.

        Returns
        -------
        ContextEntity
            Entity saved.
        """
        if update:
            return self.update()
        return ContextEntityCRUDProcessor().create_context_entity(self)

    def update(self) -> ContextEntity:
        """
        Update the entity in the backend.

        Returns
        -------
        ContextEntity
            Entity updated.
        """
        return ContextEntityCRUDProcessor().update_context_entity(self)

    def export(self) -> str:
        """
        Export object as a YAML file in the context folder.

        Returns
        -------
        str
            Exported filepath.
        """
        return ContextEntityCRUDProcessor().export_context_entity(self)

    def refresh(self) -> ContextEntity:
        """
        Refresh object from backend.

        Returns
        -------
        ContextEntity
            Entity refreshed.
        """
        return ContextEntityCRUDProcessor().refresh_context_entity(self)

    ##############################
    #  Project context
    ##############################

    def _context(self) -> Context:
        """
        Get context.

        Returns
        -------
        Context
            Context object.
        """
        return get_context(self.project)
