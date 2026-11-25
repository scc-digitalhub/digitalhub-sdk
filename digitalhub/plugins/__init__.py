# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""
Interface between the core SDK and runtime packages.

Runtimes import the base classes, mixins and helpers they extend from this
module instead of the private modules that define them, so the core can move
its internals without breaking them. A runtime registers its kinds by exposing
a tuple of ``EntityPlugin`` through an entry point in the ``digitalhub.runtimes``
group of its ``pyproject.toml``::

    [project.entry-points."digitalhub.runtimes"]
    python = "digitalhub_runtime_python:entity_plugins"
"""

from __future__ import annotations

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._base.entity.spec import Spec
from digitalhub.entities._base.entity.status import Status
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes, Relationship, State
from digitalhub.entities._commons.utils import KindAction, get_entity_type_from_key, map_actions
from digitalhub.entities._constructors.spec import build_spec
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.entities._frameworks.k8s.models import CorePort, CorePullPolicy, CoreServiceType
from digitalhub.entities._mixin.execution.spec import BuildSpecMixin, ServeSpecMixin
from digitalhub.entities._mixin.runtime_entity.builder import RuntimeEntityBuilder
from digitalhub.entities._mixin.source.builder import SourceBuilderMixin
from digitalhub.entities._mixin.source.entity import SourceEntityMixin
from digitalhub.entities._mixin.source.models import HandlerSourceCode, SourceCode
from digitalhub.entities.artifact._base.entity import Artifact
from digitalhub.entities.dataitem._base.crud import new_dataitem
from digitalhub.entities.dataitem._base.entity import Dataitem
from digitalhub.entities.function._base.builder import FunctionBuilder
from digitalhub.entities.function._base.entity import Function
from digitalhub.entities.model._base.builder import ModelBuilder
from digitalhub.entities.model._base.crud import log_base_model, register_base_model
from digitalhub.entities.model._base.entity import Model
from digitalhub.entities.model._base.spec import ModelSpec
from digitalhub.entities.model._base.status import ModelStatus
from digitalhub.entities.project._base.entity import Project
from digitalhub.entities.run._base.builder import RunBuilder
from digitalhub.entities.run._base.entity import LocalExecutionRunMixin, Run
from digitalhub.entities.run._base.spec import LocalExecutionSpecMixin, RunSpecFunction, RunSpecWorkflow
from digitalhub.entities.run._base.status import RunStatus
from digitalhub.entities.task._base.builder import TaskBuilder
from digitalhub.entities.task._base.entity import Task
from digitalhub.entities.task._base.spec import TaskSpecFunction, TaskSpecWorkflow
from digitalhub.entities.workflow._base.builder import WorkflowBuilder
from digitalhub.entities.workflow._base.entity import Workflow
from digitalhub.factory.plugins import CrudPlugin, EntityPlugin
from digitalhub.runtimes._base import Runtime
from digitalhub.runtimes.builder import RuntimeBuilder

__all__ = [
    "Artifact",
    "BuildSpecMixin",
    "ContextEntity",
    "CorePort",
    "CorePullPolicy",
    "CoreServiceType",
    "CrudPlugin",
    "Dataitem",
    "EntityKinds",
    "EntityPlugin",
    "EntityTypes",
    "Function",
    "FunctionBuilder",
    "HandlerSourceCode",
    "KindAction",
    "LocalExecutionRunMixin",
    "LocalExecutionSpecMixin",
    "Model",
    "ModelBuilder",
    "ModelSpec",
    "ModelStatus",
    "Project",
    "Relationship",
    "Run",
    "RunBuilder",
    "RunSpecFunction",
    "RunSpecWorkflow",
    "RunStatus",
    "Runtime",
    "RuntimeBuilder",
    "RuntimeEntityBuilder",
    "ServeSpecMixin",
    "SourceBuilderMixin",
    "SourceCode",
    "SourceEntityMixin",
    "Spec",
    "State",
    "Status",
    "Task",
    "TaskBuilder",
    "TaskSpecFunction",
    "TaskSpecWorkflow",
    "Workflow",
    "WorkflowBuilder",
    "build_spec",
    "build_uuid",
    "get_entity_type_from_key",
    "log_base_model",
    "map_actions",
    "new_dataitem",
    "register_base_model",
]
