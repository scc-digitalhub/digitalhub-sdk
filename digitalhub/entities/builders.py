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
from digitalhub.entities.artifact._base.entity import Artifact
from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact
from digitalhub.entities.artifact.artifact.spec import ArtifactSpecArtifact
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.containerimage._base.entity import Containerimage
from digitalhub.entities.containerimage._base.spec import ContainerimageSpec
from digitalhub.entities.containerimage._base.status import ContainerimageStatus
from digitalhub.entities.containerimage.containerimage.entity import ContainerimageContainerimage
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.dataitem._base.status import DataitemStatus
from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant
from digitalhub.entities.dataitem.dataitem.entity import DataitemDataitem
from digitalhub.entities.dataitem.table.entity import DataitemTable
from digitalhub.entities.dataitem.table.spec import DataitemSpecTable
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.function._base.entity import Function
from digitalhub.entities.log._base.builder import LogLogBuilder
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model._base.entity import Model
from digitalhub.entities.model._base.spec import ModelSpec
from digitalhub.entities.model._base.status import ModelStatus
from digitalhub.entities.model.model.entity import ModelModel
from digitalhub.entities.project._base.builder import ProjectProjectBuilder
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run._base.entity import Run
from digitalhub.entities.secret._base.builder import SecretBuilder
from digitalhub.entities.secret._base.entity import Secret
from digitalhub.entities.secret._base.spec import SecretSpec
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.task._base.entity import Task
from digitalhub.entities.trigger._base.builder import TriggerBuilder
from digitalhub.entities.trigger._base.entity import Trigger
from digitalhub.entities.trigger.lifecycle.entity import TriggerLifecycle
from digitalhub.entities.trigger.lifecycle.spec import TriggerSpecLifecycle
from digitalhub.entities.trigger.scheduler.entity import TriggerScheduler
from digitalhub.entities.trigger.scheduler.spec import TriggerSpecScheduler
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.entities.workflow._base.entity import Workflow
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

# Fallback for kinds without a builder, for example when their runtime is not
# installed: one builder per entity type, registered by type instead of by kind.
# The entity is the class of its type, so everything the backend does (wait,
# logs, runs of a function, download) keeps working; the spec and the status
# keep every field as it is.
_generic_definitions = tuple(
    BuilderDef(EntityKinds.GENERIC, entity, GenericSpec, GenericStatus, base=base, mixins=(GenericBuilder,))
    for entity, base in (
        (Artifact, ArtifactBuilder),
        (Dataitem, DataitemBuilder),
        (Containerimage, ContainerimageBuilder),
        (Function, FunctionBuilder),
        (Model, ModelBuilder),
        (Run, RunBuilder),
        (Secret, SecretBuilder),
        (Task, TaskBuilder),
        (Trigger, TriggerBuilder),
        (Workflow, WorkflowBuilder),
    )
)

generic_entity_builders: tuple = tuple(
    (definition.base.ENTITY_TYPE, definition.plugin().builder) for definition in _generic_definitions
)
