from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._base.unversioned.builder import UnversionedBuilder
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.run.generic.entity import RunGeneric


class RunGenericBuilder(GenericBuilder, UnversionedBuilder):
    """Builder for generic runs that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.RUN.value
    ENTITY_CLASS = RunGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value

    def build(
        self,
        project: str,
        kind: str,
        name: str | None = None,
        uuid: str | None = None,
        extensions: list[dict] | None = None,
        labels: list[str] | None = None,
        task: str | None = None,
        local_execution: bool = False,
        **kwargs,
    ) -> RunGeneric:
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=uuid,
            labels=labels,
        )
        spec = self.build_spec(
            task=task,
            local_execution=local_execution,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            project=project,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
            extensions=extensions,
        )
