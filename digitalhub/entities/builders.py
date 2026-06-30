# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.artifact.artifact.builder import ArtifactArtifactBuilder
from digitalhub.entities.containerimage.containerimage.builder import ContainerimageContainerimageBuilder
from digitalhub.entities.dataitem.croissant.builder import DataitemCroissantBuilder
from digitalhub.entities.dataitem.dataitem.builder import DataitemDataitemBuilder
from digitalhub.entities.dataitem.table.builder import DataitemTableBuilder
from digitalhub.entities.extension._base.builder import ExtensionExtensionBuilder
from digitalhub.entities.log._base.builder import LogLogBuilder
from digitalhub.entities.model.huggingface.builder import ModelHuggingfaceBuilder
from digitalhub.entities.model.mlflow.builder import ModelModelBuilder
from digitalhub.entities.model.model.builder import ModelMlflowBuilder
from digitalhub.entities.model.sklearn.builder import ModelSklearnBuilder
from digitalhub.entities.model.tvm_ir.builder import ModelTvmIrBuilder
from digitalhub.entities.model.tvm_so.builder import ModelTvmSoBuilder
from digitalhub.entities.project._base.builder import ProjectProjectBuilder
from digitalhub.entities.secret._base.builder import SecretSecretBuilder
from digitalhub.entities.trigger.automl.builder import TriggerAutomlBuilder
from digitalhub.entities.trigger.lifecycle.builder import TriggerLifecycleBuilder
from digitalhub.entities.trigger.scheduler.builder import TriggerSchedulerBuilder

entity_builders: tuple = (
    (ArtifactArtifactBuilder.ENTITY_KIND, ArtifactArtifactBuilder),
    (ContainerimageContainerimageBuilder.ENTITY_KIND, ContainerimageContainerimageBuilder),
    (DataitemCroissantBuilder.ENTITY_KIND, DataitemCroissantBuilder),
    (DataitemDataitemBuilder.ENTITY_KIND, DataitemDataitemBuilder),
    (DataitemTableBuilder.ENTITY_KIND, DataitemTableBuilder),
    (ExtensionExtensionBuilder.ENTITY_KIND, ExtensionExtensionBuilder),
    (LogLogBuilder.ENTITY_KIND, LogLogBuilder),
    (ModelHuggingfaceBuilder.ENTITY_KIND, ModelHuggingfaceBuilder),
    (ModelMlflowBuilder.ENTITY_KIND, ModelMlflowBuilder),
    (ModelModelBuilder.ENTITY_KIND, ModelModelBuilder),
    (ModelSklearnBuilder.ENTITY_KIND, ModelSklearnBuilder),
    (ModelTvmIrBuilder.ENTITY_KIND, ModelTvmIrBuilder),
    (ModelTvmSoBuilder.ENTITY_KIND, ModelTvmSoBuilder),
    (ProjectProjectBuilder.ENTITY_KIND, ProjectProjectBuilder),
    (SecretSecretBuilder.ENTITY_KIND, SecretSecretBuilder),
    (TriggerAutomlBuilder.ENTITY_KIND, TriggerAutomlBuilder),
    (TriggerLifecycleBuilder.ENTITY_KIND, TriggerLifecycleBuilder),
    (TriggerSchedulerBuilder.ENTITY_KIND, TriggerSchedulerBuilder),
)
