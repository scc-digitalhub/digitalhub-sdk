# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities import crud_plugins as _crud_plugins
from digitalhub.entities._base.entity.status import Status
from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities._mixin.generic.builder import GenericBuilder
from digitalhub.entities._mixin.generic.spec import GenericSpec
from digitalhub.entities._mixin.generic.status import GenericStatus
from digitalhub.entities._mixin.material.spec import MaterialSpec
from digitalhub.entities._mixin.material.status import MaterialStatus
from digitalhub.entities.artifact._base.builder import ArtifactBuilder
from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact
from digitalhub.entities.artifact.artifact.spec import ArtifactSpecArtifact
from digitalhub.entities.artifact.generic.entity import ArtifactGeneric
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.containerimage._base.spec import ContainerimageSpec
from digitalhub.entities.containerimage._base.status import ContainerimageStatus
from digitalhub.entities.containerimage.containerimage.entity import ContainerimageContainerimage
from digitalhub.entities.containerimage.generic.entity import ContainerimageGeneric
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem._base.status import DataitemStatus
from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant
from digitalhub.entities.dataitem.dataitem.entity import DataitemDataitem
from digitalhub.entities.dataitem.generic.entity import DataitemGeneric
from digitalhub.entities.dataitem.table.entity import DataitemTable
from digitalhub.entities.dataitem.table.spec import DataitemSpecTable
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.function.generic.entity import FunctionGeneric
from digitalhub.entities.log._base.builder import LogLogBuilder
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model._base.spec import ModelSpec
from digitalhub.entities.model._base.status import ModelStatus
from digitalhub.entities.model.generic.entity import ModelGeneric
from digitalhub.entities.model.model.entity import ModelModel
from digitalhub.entities.project._base.builder import ProjectProjectBuilder
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run.generic.entity import RunGeneric
from digitalhub.entities.secret._base.builder import SecretBuilder
from digitalhub.entities.secret._base.entity import Secret
from digitalhub.entities.secret._base.spec import SecretSpec
from digitalhub.entities.secret.generic.entity import SecretGeneric
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.task.generic.entity import TaskGeneric
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger.generic.entity import TriggerGeneric
from digitalhub.entities.trigger.lifecycle.entity import TriggerLifecycle
from digitalhub.entities.trigger.lifecycle.spec import TriggerSpecLifecycle
from digitalhub.entities.trigger.scheduler.entity import TriggerScheduler
from digitalhub.entities.trigger.scheduler.spec import TriggerSpecScheduler
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.entities.workflow.generic.entity import WorkflowGeneric
from digitalhub.factory.builders import BuilderDef
from digitalhub.factory.plugins import EntityPlugin

crud_plugins = _crud_plugins

# Kinds made only of entity, spec and status: their builders are generated.
_definitions = (
    BuilderDef(
        EntityKinds.ARTIFACT_ARTIFACT,
        ArtifactArtifact,
        ArtifactSpecArtifact,
        MaterialStatus,
        base=ArtifactBuilder,
    ),
    BuilderDef(
        EntityKinds.CONTAINERIMAGE_CONTAINERIMAGE,
        ContainerimageContainerimage,
        ContainerimageSpec,
        ContainerimageStatus,
        base=ContainerimageBuilder,
    ),
    BuilderDef(EntityKinds.DATAITEM_CROISSANT, DataitemCroissant, MaterialSpec, DataitemStatus, base=DataitemBuilder),
    BuilderDef(EntityKinds.DATAITEM_DATAITEM, DataitemDataitem, MaterialSpec, DataitemStatus, base=DataitemBuilder),
    BuilderDef(EntityKinds.DATAITEM_TABLE, DataitemTable, DataitemSpecTable, DataitemStatus, base=DataitemBuilder),
    BuilderDef(EntityKinds.MODEL_MODEL, ModelModel, ModelSpec, ModelStatus, base=ModelBuilder),
    BuilderDef(EntityKinds.SECRET_SECRET, Secret, SecretSpec, Status, base=SecretBuilder),
    BuilderDef(EntityKinds.TRIGGER_LIFECYCLE, TriggerLifecycle, TriggerSpecLifecycle, Status, base=TriggerBuilder),
    BuilderDef(EntityKinds.TRIGGER_SCHEDULER, TriggerScheduler, TriggerSpecScheduler, Status, base=TriggerBuilder),
)

entity_plugins: tuple[EntityPlugin, ...] = (
    *(definition.plugin() for definition in _definitions),
    # These builders carry their own logic.
    EntityPlugin(builder=LogLogBuilder),
    EntityPlugin(builder=ProjectProjectBuilder),
)

# Fallback for kinds without a builder: one generic builder per entity type,
# registered by type instead of by kind.
_generic_definitions = tuple(
    BuilderDef(EntityKinds.GENERIC, entity, GenericSpec, GenericStatus, base=base, mixins=(GenericBuilder,))
    for entity, base in (
        (ArtifactGeneric, ArtifactBuilder),
        (DataitemGeneric, DataitemBuilder),
        (ContainerimageGeneric, ContainerimageBuilder),
        (FunctionGeneric, FunctionBuilder),
        (ModelGeneric, ModelBuilder),
        (RunGeneric, RunBuilder),
        (SecretGeneric, SecretBuilder),
        (TaskGeneric, TaskBuilder),
        (TriggerGeneric, TriggerBuilder),
        (WorkflowGeneric, WorkflowBuilder),
    )
)

generic_entity_builders: tuple = tuple(
    (definition.base.ENTITY_TYPE, definition.plugin().builder) for definition in _generic_definitions
)
