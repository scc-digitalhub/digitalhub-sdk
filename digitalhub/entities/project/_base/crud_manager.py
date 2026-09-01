# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities import OPS_REGISTRY, EntityOperation
from digitalhub.entities._commons.enums import EntityTypes, OpType

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.artifact._base.entity import Artifact  # noqa: F401
    from digitalhub.entities.artifact.artifact.entity import ArtifactArtifact
    from digitalhub.entities.containerimage._base.entity import Containerimage
    from digitalhub.entities.dataitem._base.entity import Dataitem  # noqa: F401
    from digitalhub.entities.dataitem.croissant.entity import DataitemCroissant
    from digitalhub.entities.dataitem.dataitem.entity import DataitemDataitem
    from digitalhub.entities.dataitem.table.entity import DataitemTable
    from digitalhub.entities.function._base.entity import Function
    from digitalhub.entities.model._base.entity import Model  # noqa: F401
    from digitalhub.entities.model.huggingface.entity import ModelHuggingface
    from digitalhub.entities.model.mlflow.entity import ModelMlflow
    from digitalhub.entities.model.model.entity import ModelModel
    from digitalhub.entities.model.sklearn.entity import ModelSklearn
    from digitalhub.entities.model.tvm_ir.entity import ModelTvmIr
    from digitalhub.entities.model.tvm_so.entity import ModelTvmSo
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.secret._base.entity import Secret
    from digitalhub.entities.task._base.entity import Task
    from digitalhub.entities.trigger._base.entity import Trigger
    from digitalhub.entities.workflow._base.entity import Workflow

EntityT = typing.TypeVar("EntityT", bound="ContextEntity")


class EntityCRUD(typing.Generic[EntityT]):
    """Base manager for entity CRUD operations."""

    def __init__(self, project_name: str, entity_type: EntityTypes) -> None:
        """
        Initialize CRUD manager.

        Parameters
        ----------
        project_name : str
            Name of the project.
        entity_type : EntityTypes
            Type of entity.
        """
        self.project_name = project_name
        self.entity_type = entity_type
        self._ops: dict[OpType, EntityOperation] = OPS_REGISTRY[entity_type]

    def _inject_project(self, kwargs: dict) -> dict:
        """
        Inject project name into kwargs.

        Parameters
        ----------
        kwargs : dict
            Keyword arguments.

        Returns
        -------
        dict
            Kwargs with project name injected.
        """
        kwargs.setdefault("project", self.project_name)
        return kwargs

    def _call_op(self, op_type: OpType, *args, **kwargs) -> object:
        """
        Call an operation by type.

        Parameters
        ----------
        op_type : OpType
            Operation type.
        *args
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        object
            Result of the operation.
        """
        op = self._ops.get(op_type)
        if op is None:
            raise AttributeError(f"Operation '{op_type.value}' not available for {self.entity_type.value}")
        return op(*args, **self._inject_project(kwargs))

    def new(self, **kwargs) -> EntityT:
        """Create a new entity."""
        return typing.cast("EntityT", self._call_op(OpType.NEW, **kwargs))

    def log(self, **kwargs) -> EntityT:
        """Create and upload an entity."""
        return typing.cast("EntityT", self._call_op(OpType.LOG_GENERIC, **kwargs))

    def register(self, **kwargs) -> EntityT:
        """Register an entity that already exists in a supported store."""
        return typing.cast("EntityT", self._call_op(OpType.REGISTER_GENERIC, **kwargs))

    def get(self, *args, **kwargs) -> EntityT:
        """Get entity from backend."""
        return typing.cast("EntityT", self._call_op(OpType.GET, *args, **kwargs))

    def get_versions(self, *args, **kwargs) -> list[EntityT]:
        """Get entity versions from backend."""
        return typing.cast("list[EntityT]", self._call_op(OpType.GET_VERSIONS, *args, **kwargs))

    def list(self, **kwargs) -> list[EntityT]:
        """List all latest version entities from backend."""
        return typing.cast("list[EntityT]", self._ops[OpType.LIST](self.project_name, **kwargs))

    def import_entity(self, **kwargs) -> EntityT:
        """Import entity from a YAML file or key."""
        kwargs["context"] = self.project_name
        return typing.cast("EntityT", self._ops[OpType.IMPORT](**kwargs))

    def load(self, *args, **kwargs) -> EntityT:
        """Load entity from backend."""
        return typing.cast("EntityT", self._call_op(OpType.LOAD, *args, **kwargs))

    def update(self, entity: EntityT) -> EntityT:
        """Update entity."""
        if entity.project != self.project_name:
            raise ValueError(f"Entity to update is not in project {self.project_name}.")
        return typing.cast("EntityT", self._ops[OpType.UPDATE](entity))

    def delete(self, *args, **kwargs) -> dict:
        """Delete entity from backend."""
        return typing.cast(dict, self._call_op(OpType.DELETE, *args, **kwargs))


class EntityCRUDArtifact(EntityCRUD["Artifact"]):
    """CRUD manager for artifact entities."""

    def log_artifact(self, **kwargs) -> ArtifactArtifact:
        """Create and upload an artifact entity."""
        return typing.cast("ArtifactArtifact", self._call_op(OpType.LOG_ARTIFACT, **kwargs))

    def register_artifact(self, **kwargs) -> ArtifactArtifact:
        """Register an artifact entity."""
        return typing.cast("ArtifactArtifact", self._call_op(OpType.REGISTER_ARTIFACT, **kwargs))


class EntityCRUDDataitem(EntityCRUD["Dataitem"]):
    """CRUD manager for dataitem entities."""

    def log_dataitem(self, **kwargs) -> DataitemDataitem:
        """Create and upload a dataitem entity."""
        return typing.cast("DataitemDataitem", self._call_op(OpType.LOG_DATAITEM, **kwargs))

    def log_table(self, **kwargs) -> DataitemTable:
        """Create and upload a table dataitem entity."""
        return typing.cast("DataitemTable", self._call_op(OpType.LOG_TABLE, **kwargs))

    def log_croissant(self, **kwargs) -> DataitemCroissant:
        """Create and upload a Croissant model entity."""
        return typing.cast("DataitemCroissant", self._call_op(OpType.LOG_CROISSANT, **kwargs))

    def register_dataitem(self, **kwargs) -> DataitemDataitem:
        """Register a dataitem entity."""
        return typing.cast("DataitemDataitem", self._call_op(OpType.REGISTER_DATAITEM, **kwargs))

    def register_table(self, **kwargs) -> DataitemTable:
        """Register a table dataitem entity."""
        return typing.cast("DataitemTable", self._call_op(OpType.REGISTER_TABLE, **kwargs))

    def register_croissant(self, **kwargs) -> DataitemCroissant:
        """Register a Croissant dataitem entity."""
        return typing.cast("DataitemCroissant", self._call_op(OpType.REGISTER_CROISSANT, **kwargs))


class EntityCRUDModel(EntityCRUD["Model"]):
    """CRUD manager for model entities."""

    def log_model(self, **kwargs) -> ModelModel:
        """Create and upload a model entity."""
        return typing.cast("ModelModel", self._call_op(OpType.LOG_MODEL, **kwargs))

    def log_mlflow(self, **kwargs) -> ModelMlflow:
        """Create and upload a MLflow model entity."""
        return typing.cast("ModelMlflow", self._call_op(OpType.LOG_MLFLOW, **kwargs))

    def log_sklearn(self, **kwargs) -> ModelSklearn:
        """Create and upload a scikit-learn model entity."""
        return typing.cast("ModelSklearn", self._call_op(OpType.LOG_SKLEARN, **kwargs))

    def log_huggingface(self, **kwargs) -> ModelHuggingface:
        """Create and upload a Huggingface model entity."""
        return typing.cast("ModelHuggingface", self._call_op(OpType.LOG_HUGGINGFACE, **kwargs))

    def log_tvm_ir(self, **kwargs) -> ModelTvmIr:
        """Create and upload a TVM IR model entity."""
        return typing.cast("ModelTvmIr", self._call_op(OpType.LOG_TVM_IR, **kwargs))

    def log_tvm_so(self, **kwargs) -> ModelTvmSo:
        """Create and upload a TVM SO model entity."""
        return typing.cast("ModelTvmSo", self._call_op(OpType.LOG_TVM_SO, **kwargs))

    def register_model(self, **kwargs) -> ModelModel:
        """Register a model entity."""
        return typing.cast("ModelModel", self._call_op(OpType.REGISTER_MODEL, **kwargs))

    def register_mlflow(self, **kwargs) -> ModelMlflow:
        """Register a MLflow model entity."""
        return typing.cast("ModelMlflow", self._call_op(OpType.REGISTER_MLFLOW, **kwargs))

    def register_sklearn(self, **kwargs) -> ModelSklearn:
        """Register a scikit-learn model entity."""
        return typing.cast("ModelSklearn", self._call_op(OpType.REGISTER_SKLEARN, **kwargs))

    def register_huggingface(self, **kwargs) -> ModelHuggingface:
        """Register a Huggingface model entity."""
        return typing.cast("ModelHuggingface", self._call_op(OpType.REGISTER_HUGGINGFACE, **kwargs))

    def register_tvm_ir(self, **kwargs) -> ModelTvmIr:
        """Register a TVM IR model entity."""
        return typing.cast("ModelTvmIr", self._call_op(OpType.REGISTER_TVM_IR, **kwargs))

    def register_tvm_so(self, **kwargs) -> ModelTvmSo:
        """Register a TVM SO model entity."""
        return typing.cast("ModelTvmSo", self._call_op(OpType.REGISTER_TVM_SO, **kwargs))


class CRUDManager:
    """
    Manager for CRUD operations on all entity types.
    """

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        self.artifact = EntityCRUDArtifact(project_name, EntityTypes.ARTIFACT)
        self.dataitem = EntityCRUDDataitem(project_name, EntityTypes.DATAITEM)
        self.model = EntityCRUDModel(project_name, EntityTypes.MODEL)
        self.function: EntityCRUD[Function] = EntityCRUD(project_name, EntityTypes.FUNCTION)
        self.workflow: EntityCRUD[Workflow] = EntityCRUD(project_name, EntityTypes.WORKFLOW)
        self.task: EntityCRUD[Task] = EntityCRUD(project_name, EntityTypes.TASK)
        self.run: EntityCRUD[Run] = EntityCRUD(project_name, EntityTypes.RUN)
        self.trigger: EntityCRUD[Trigger] = EntityCRUD(project_name, EntityTypes.TRIGGER)
        self.secret: EntityCRUD[Secret] = EntityCRUD(project_name, EntityTypes.SECRET)
        self.containerimage: EntityCRUD[Containerimage] = EntityCRUD(project_name, EntityTypes.CONTAINERIMAGE)
