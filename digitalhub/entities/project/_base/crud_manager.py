# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from enum import Enum

from digitalhub import entities
from digitalhub.entities._commons.enums import EntityTypes


class OpType(str, Enum):
    """Enum for CRUD operation types."""

    NEW = "new"
    LOG = "log"
    LOG_GENERIC = "log_generic"
    LOG_TABLE = "log_table"
    LOG_MLFLOW = "log_mlflow"
    LOG_SKLEARN = "log_sklearn"
    LOG_HUGGINGFACE = "log_huggingface"
    GET = "get"
    GET_VERSIONS = "get_versions"
    LIST = "list"
    IMPORT = "import"
    UPDATE = "update"
    DELETE = "delete"


# Operation registry: maps entity type to operation functions
OPS_REGISTRY = {
    EntityTypes.ARTIFACT: {
        OpType.NEW: entities.new_artifact,
        OpType.LOG: entities.log_artifact,
        OpType.LOG_GENERIC: entities.log_generic_artifact,
        OpType.GET: entities.get_artifact,
        OpType.GET_VERSIONS: entities.get_artifact_versions,
        OpType.LIST: entities.list_artifacts,
        OpType.IMPORT: entities.import_artifact,
        OpType.UPDATE: entities.update_artifact,
        OpType.DELETE: entities.delete_artifact,
    },
    EntityTypes.DATAITEM: {
        OpType.NEW: entities.new_dataitem,
        OpType.LOG: entities.log_dataitem,
        OpType.LOG_GENERIC: entities.log_generic_dataitem,
        OpType.LOG_TABLE: entities.log_table,
        OpType.GET: entities.get_dataitem,
        OpType.GET_VERSIONS: entities.get_dataitem_versions,
        OpType.LIST: entities.list_dataitems,
        OpType.IMPORT: entities.import_dataitem,
        OpType.UPDATE: entities.update_dataitem,
        OpType.DELETE: entities.delete_dataitem,
    },
    EntityTypes.MODEL: {
        OpType.NEW: entities.new_model,
        OpType.LOG: entities.log_model,
        OpType.LOG_GENERIC: entities.log_generic_model,
        OpType.LOG_MLFLOW: entities.log_mlflow,
        OpType.LOG_SKLEARN: entities.log_sklearn,
        OpType.LOG_HUGGINGFACE: entities.log_huggingface,
        OpType.GET: entities.get_model,
        OpType.GET_VERSIONS: entities.get_model_versions,
        OpType.LIST: entities.list_models,
        OpType.IMPORT: entities.import_model,
        OpType.UPDATE: entities.update_model,
        OpType.DELETE: entities.delete_model,
    },
    EntityTypes.FUNCTION: {
        OpType.NEW: entities.new_function,
        OpType.GET: entities.get_function,
        OpType.GET_VERSIONS: entities.get_function_versions,
        OpType.LIST: entities.list_functions,
        OpType.IMPORT: entities.import_function,
        OpType.UPDATE: entities.update_function,
        OpType.DELETE: entities.delete_function,
    },
    EntityTypes.WORKFLOW: {
        OpType.NEW: entities.new_workflow,
        OpType.GET: entities.get_workflow,
        OpType.GET_VERSIONS: entities.get_workflow_versions,
        OpType.LIST: entities.list_workflows,
        OpType.IMPORT: entities.import_workflow,
        OpType.UPDATE: entities.update_workflow,
        OpType.DELETE: entities.delete_workflow,
    },
    EntityTypes.SECRET: {
        OpType.NEW: entities.new_secret,
        OpType.GET: entities.get_secret,
        OpType.LIST: entities.list_secrets,
        OpType.IMPORT: entities.import_secret,
        OpType.UPDATE: entities.update_secret,
        OpType.DELETE: entities.delete_secret,
    },
    EntityTypes.RUN: {
        OpType.GET: entities.get_run,
        OpType.LIST: entities.list_runs,
        OpType.DELETE: entities.delete_run,
    },
}


class EntityCRUD:
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
        self._ops = OPS_REGISTRY[entity_type]

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

    def _call_op(self, op_type: OpType, *args, **kwargs):
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
        Any
            Result of the operation.
        """
        op = self._ops.get(op_type)
        if op is None:
            raise AttributeError(f"Operation '{op_type.value}' not available for {self.entity_type.value}")
        return op(*args, **self._inject_project(kwargs))

    def new(self, **kwargs):
        """Create a new entity."""
        return self._call_op(OpType.NEW, **kwargs)

    def log(self, **kwargs):
        """Create and upload an entity."""
        return self._call_op(OpType.LOG, **kwargs)

    def log_generic(self, **kwargs):
        """Create and upload a generic entity."""
        return self._call_op(OpType.LOG_GENERIC, **kwargs)

    def log_table(self, **kwargs):
        """Create and upload a table dataitem."""
        return self._call_op(OpType.LOG_TABLE, **kwargs)

    def log_mlflow(self, **kwargs):
        """Create and upload a MLflow model."""
        return self._call_op(OpType.LOG_MLFLOW, **kwargs)

    def log_sklearn(self, **kwargs):
        """Create and upload a scikit-learn model."""
        return self._call_op(OpType.LOG_SKLEARN, **kwargs)

    def log_huggingface(self, **kwargs):
        """Create and upload a Huggingface model."""
        return self._call_op(OpType.LOG_HUGGINGFACE, **kwargs)

    def get(self, identifier: str, **kwargs):
        """Get entity from backend."""
        return self._call_op(OpType.GET, identifier, **kwargs)

    def get_versions(self, identifier: str, **kwargs):
        """Get entity versions from backend."""
        return self._call_op(OpType.GET_VERSIONS, identifier, **kwargs)

    def list(self, **kwargs):
        """List all latest version entities from backend."""
        # list() is special - project is first positional arg
        kwargs = self._inject_project(kwargs)
        return self._ops[OpType.LIST](kwargs.pop("project"), **kwargs)

    def import_entity(self, file: str | None = None, key: str | None = None, **kwargs):
        """Import entity from a YAML file or key."""
        return self._call_op(OpType.IMPORT, file, key, **self._inject_project(kwargs))

    def update(self, entity):
        """Update entity."""
        return self._ops[OpType.UPDATE](entity)

    def delete(self, identifier: str, **kwargs):
        """Delete entity from backend."""
        return self._call_op(OpType.DELETE, identifier, **kwargs)


class CRUDManager:
    """
    Manager for CRUD operations on all entity types.

    Provides convenient access to CRUD operations for artifacts, dataitems,
    models, functions, workflows, secrets, and runs within a project.

    Parameters
    ----------
    project_name : str
        Name of the project.

    Examples
    --------
    >>> manager = CRUDManager("my-project")
    >>> artifact = manager.artifact.new(name="my-artifact", kind="artifact")
    >>> artifacts = manager.artifact.list()
    >>> model = manager.model.log_mlflow(name="my-model", source="path/to/model")
    """

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        self.artifact = EntityCRUD(project_name, EntityTypes.ARTIFACT)
        self.dataitem = EntityCRUD(project_name, EntityTypes.DATAITEM)
        self.model = EntityCRUD(project_name, EntityTypes.MODEL)
        self.function = EntityCRUD(project_name, EntityTypes.FUNCTION)
        self.workflow = EntityCRUD(project_name, EntityTypes.WORKFLOW)
        self.secret = EntityCRUD(project_name, EntityTypes.SECRET)
        self.run = EntityCRUD(project_name, EntityTypes.RUN)
