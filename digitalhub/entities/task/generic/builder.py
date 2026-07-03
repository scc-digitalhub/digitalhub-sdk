from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._base.unversioned.builder import UnversionedBuilder
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.task.generic.entity import TaskGeneric


class TaskGenericBuilder(GenericBuilder, UnversionedBuilder):
    """Builder for generic tasks that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.TASK.value
    ENTITY_CLASS = TaskGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value

    def build(
        self,
        project: str,
        kind: str,
        uuid: str | None = None,
        labels: list[str] | None = None,
        **kwargs,
    ) -> TaskGeneric:
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=uuid,
            labels=labels,
        )
        spec = self.build_spec(**kwargs)
        status = self.build_status()
        return self.build_entity(
            project=project,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )
