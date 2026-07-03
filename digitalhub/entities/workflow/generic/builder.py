from __future__ import annotations

from digitalhub.entities._base.entity.spec import SpecValidator
from digitalhub.entities._base.generic.builder import GenericBuilder
from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.entities.workflow.generic.entity import WorkflowGeneric


class WorkflowGenericBuilder(GenericBuilder, WorkflowBuilder):
    """Builder for generic workflows that preserves arbitrary payload fields."""

    ENTITY_TYPE = EntityTypes.WORKFLOW.value
    ENTITY_CLASS = WorkflowGeneric
    ENTITY_SPEC_CLASS = GenericSpec
    ENTITY_SPEC_VALIDATOR = SpecValidator
    ENTITY_STATUS_CLASS = GenericStatus
    ENTITY_KIND = EntityKinds.GENERIC.value
