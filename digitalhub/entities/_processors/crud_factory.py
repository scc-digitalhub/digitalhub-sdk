# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, Protocol, TypeVar, cast

from digitalhub.entities._commons.utils import build_log_name_from_source
from digitalhub.entities._mixin.material.utils import build_register_name, kind_warning
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor
from digitalhub.utils.file_utils import eval_local_source
from digitalhub.utils.types import SourcesOrListOfSources


class CRUDContextEntity(Protocol):
    """Structural contract needed by shared context entity operations."""

    project: str
    ENTITY_TYPE: str
    id: str

    def to_dict(self) -> dict: ...


EntityT = TypeVar("EntityT", bound=CRUDContextEntity)


class ContextEntityCRUD(Generic[EntityT]):
    """Shared CRUD operations for typed context entity shortcut modules."""

    def __init__(
        self,
        entity_type: str,
        *,
        unversioned: bool = False,
        executable: bool = False,
    ) -> None:
        self.entity_type = entity_type
        self.unversioned = unversioned
        self.executable = executable

    def create(self, **kwargs: Any) -> EntityT:
        return cast(
            EntityT,
            ContextEntityCRUDProcessor().create_context_entity_from_params(entity_type=self.entity_type, **kwargs),
        )

    def get(
        self,
        identifier: str,
        project: str | None = None,
        entity_id: str | None = None,
    ) -> EntityT:
        processor = ContextEntityCRUDProcessor()
        reader = processor.read_unversioned_entity if self.unversioned else processor.read_context_entity
        read_kwargs = {
            "identifier": identifier,
            "entity_type": self.entity_type,
            "project": project,
        }
        if not self.unversioned or entity_id is not None:
            read_kwargs["entity_id"] = entity_id
        return cast(
            EntityT,
            reader(**read_kwargs),
        )

    def get_versions(self, identifier: str, project: str | None = None) -> list[EntityT]:
        return cast(
            list[EntityT],
            ContextEntityCRUDProcessor().read_context_entity_versions(
                identifier=identifier,
                entity_type=self.entity_type,
                project=project,
            ),
        )

    def list(self, project: str, **filters: Any) -> list[EntityT]:
        return cast(
            list[EntityT],
            ContextEntityCRUDProcessor().list_context_entities(
                project=project, entity_type=self.entity_type, **filters
            ),
        )

    def import_entity(
        self,
        file: str | None = None,
        key: str | None = None,
        reset_id: bool = False,
        context: str | None = None,
    ) -> EntityT:
        if self.executable:
            return cast(
                EntityT,
                ContextEntityExecutableProcessor().import_executable_entity(file, key, reset_id, context),
            )
        return cast(EntityT, ContextEntityCRUDProcessor().import_context_entity(file, key, reset_id, context))

    def load(self, file: str) -> EntityT:
        if self.executable:
            return cast(EntityT, ContextEntityExecutableProcessor().load_executable_entity(file))
        return cast(EntityT, ContextEntityCRUDProcessor().load_context_entity(file))

    def update(self, entity: EntityT) -> EntityT:
        return cast(
            EntityT,
            ContextEntityCRUDProcessor().update_context_entity(
                project=entity.project,
                entity_type=entity.ENTITY_TYPE,
                entity_id=entity.id,
                entity_dict=entity.to_dict(),
            ),
        )

    def delete(
        self,
        identifier: str,
        project: str | None = None,
        entity_id: str | None = None,
        **options: Any,
    ) -> dict:
        if self.unversioned:
            options["unversioned"] = True
        return ContextEntityCRUDProcessor().delete_context_entity(
            identifier=identifier,
            entity_type=self.entity_type,
            project=project,
            entity_id=entity_id,
            **options,
        )


class MaterialEntityCRUD(ContextEntityCRUD[EntityT]):
    """Shared create, log, and register operations for material entities."""

    def log(
        self,
        *,
        project: str,
        kind: str,
        source: SourcesOrListOfSources,
        name: str | None = None,
        drop_existing: bool = False,
        path: str | None = None,
        version: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        **kwargs: Any,
    ) -> EntityT:
        kwargs = {key: value for key, value in kwargs.items() if value is not None}
        eval_local_source(source)
        if name is None:
            name = build_log_name_from_source(source)
        kwargs = ContextEntityMaterialProcessor().build_log_kwargs(
            project,
            name,
            entity_type=self.entity_type,
            source=source,
            path=path,
            **kwargs,
        )
        return cast(
            EntityT,
            ContextEntityMaterialProcessor().log_material_entity(
                source=source,
                project=project,
                name=name,
                kind=kind,
                drop_existing=drop_existing,
                entity_type=self.entity_type,
                version=version,
                description=description,
                labels=labels,
                **kwargs,
            ),
        )

    def register(
        self,
        create_entity: Callable[..., EntityT],
        *,
        project: str,
        source: SourcesOrListOfSources,
        entity_kind: str,
        name: str | None = None,
        uuid: str | None = None,
        version: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        extensions: list[dict] | None = None,
        **kwargs: Any,
    ) -> EntityT:
        kwargs = {key: value for key, value in kwargs.items() if value is not None}
        kind_warning(
            requested_kind=kwargs.pop("kind", None),
            set_kind=entity_kind,
            entity_type=self.entity_type,
        )
        name = build_register_name(
            name=name,
            source=source,
            entity_type=self.entity_type,
            entity_kind=entity_kind,
        )
        if isinstance(source, list):
            source = source[0]
        return create_entity(
            project=project,
            name=name,
            kind=entity_kind,
            uuid=uuid,
            version=version,
            description=description,
            labels=labels,
            embedded=embedded,
            path=source,
            extensions=extensions,
            **kwargs,
        )
