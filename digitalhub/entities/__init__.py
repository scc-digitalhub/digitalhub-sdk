# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from digitalhub.entities._commons.enums import EntityTypes, OpType
from digitalhub.entities.artifact.artifact.crud import log_artifact
from digitalhub.entities.artifact.crud import (
    delete_artifact,
    get_artifact,
    get_artifact_versions,
    import_artifact,
    list_artifacts,
    load_artifact,
    new_artifact,
    update_artifact,
)
from digitalhub.entities.artifact.generic.crud import log_generic_artifact
from digitalhub.entities.containerimage.crud import (
    delete_containerimage,
    get_containerimage,
    get_containerimage_versions,
    import_containerimage,
    list_containerimages,
    load_containerimage,
    new_containerimage,
    update_containerimage,
)
from digitalhub.entities.dataitem.croissant.crud import log_croissant
from digitalhub.entities.dataitem.crud import (
    delete_dataitem,
    get_dataitem,
    get_dataitem_versions,
    import_dataitem,
    list_dataitems,
    load_dataitem,
    new_dataitem,
    update_dataitem,
)
from digitalhub.entities.dataitem.dataitem.crud import log_dataitem
from digitalhub.entities.dataitem.generic.crud import log_generic_dataitem
from digitalhub.entities.dataitem.table.crud import log_table
from digitalhub.entities.function.crud import (
    delete_function,
    get_function,
    get_function_versions,
    import_function,
    list_functions,
    load_function,
    new_function,
    update_function,
)
from digitalhub.entities.model.crud import (
    delete_model,
    get_model,
    get_model_versions,
    import_model,
    list_models,
    load_model,
    new_model,
    update_model,
)
from digitalhub.entities.model.generic.crud import log_generic_model
from digitalhub.entities.model.huggingface.crud import log_huggingface
from digitalhub.entities.model.mlflow.crud import log_mlflow
from digitalhub.entities.model.model.crud import log_model
from digitalhub.entities.model.sklearn.crud import log_sklearn
from digitalhub.entities.model.tvm_ir.crud import log_tvm_ir
from digitalhub.entities.model.tvm_so.crud import log_tvm_so
from digitalhub.entities.project.crud import (
    delete_project,
    get_or_create_project,
    get_project,
    import_project,
    list_projects,
    load_project,
    new_project,
    search_entity,
    update_project,
)
from digitalhub.entities.run.crud import delete_run, get_run, import_run, list_runs, load_run, new_run, update_run
from digitalhub.entities.secret.crud import (
    delete_secret,
    get_secret,
    import_secret,
    list_secrets,
    load_secret,
    new_secret,
    update_secret,
)
from digitalhub.entities.task.crud import (
    delete_task,
    get_task,
    import_task,
    list_tasks,
    load_task,
    new_task,
    update_task,
)
from digitalhub.entities.trigger.crud import (
    delete_trigger,
    get_trigger,
    import_trigger,
    list_triggers,
    load_trigger,
    new_trigger,
    update_trigger,
)
from digitalhub.entities.workflow.crud import (
    delete_workflow,
    get_workflow,
    get_workflow_versions,
    import_workflow,
    list_workflows,
    load_workflow,
    new_workflow,
    update_workflow,
)

# Operation registry: maps entity type to operation functions
OPS_REGISTRY = {
    EntityTypes.ARTIFACT: {
        OpType.NEW: new_artifact,
        OpType.LOG_GENERIC: log_generic_artifact,
        OpType.LOG_ARTIFACT: log_artifact,
        OpType.IMPORT: import_artifact,
        OpType.LOAD: load_artifact,
        OpType.GET: get_artifact,
        OpType.GET_VERSIONS: get_artifact_versions,
        OpType.LIST: list_artifacts,
        OpType.UPDATE: update_artifact,
        OpType.DELETE: delete_artifact,
    },
    EntityTypes.DATAITEM: {
        OpType.NEW: new_dataitem,
        OpType.LOG_GENERIC: log_generic_dataitem,
        OpType.LOG_DATAITEM: log_dataitem,
        OpType.LOG_TABLE: log_table,
        OpType.LOG_CROISSANT: log_croissant,
        OpType.IMPORT: import_dataitem,
        OpType.LOAD: load_dataitem,
        OpType.GET: get_dataitem,
        OpType.GET_VERSIONS: get_dataitem_versions,
        OpType.LIST: list_dataitems,
        OpType.UPDATE: update_dataitem,
        OpType.DELETE: delete_dataitem,
    },
    EntityTypes.MODEL: {
        OpType.NEW: new_model,
        OpType.LOG_GENERIC: log_generic_model,
        OpType.LOG_MODEL: log_model,
        OpType.LOG_MLFLOW: log_mlflow,
        OpType.LOG_SKLEARN: log_sklearn,
        OpType.LOG_HUGGINGFACE: log_huggingface,
        OpType.LOG_TVM_IR: log_tvm_ir,
        OpType.LOG_TVM_SO: log_tvm_so,
        OpType.IMPORT: import_model,
        OpType.LOAD: load_model,
        OpType.GET: get_model,
        OpType.GET_VERSIONS: get_model_versions,
        OpType.LIST: list_models,
        OpType.UPDATE: update_model,
        OpType.DELETE: delete_model,
    },
    EntityTypes.FUNCTION: {
        OpType.NEW: new_function,
        OpType.IMPORT: import_function,
        OpType.LOAD: load_function,
        OpType.GET: get_function,
        OpType.GET_VERSIONS: get_function_versions,
        OpType.LIST: list_functions,
        OpType.UPDATE: update_function,
        OpType.DELETE: delete_function,
    },
    EntityTypes.WORKFLOW: {
        OpType.NEW: new_workflow,
        OpType.IMPORT: import_workflow,
        OpType.LOAD: load_workflow,
        OpType.GET: get_workflow,
        OpType.GET_VERSIONS: get_workflow_versions,
        OpType.LIST: list_workflows,
        OpType.UPDATE: update_workflow,
        OpType.DELETE: delete_workflow,
    },
    EntityTypes.TASK: {
        OpType.NEW: new_task,
        OpType.IMPORT: import_task,
        OpType.LOAD: load_task,
        OpType.GET: get_task,
        OpType.LIST: list_tasks,
        OpType.UPDATE: update_task,
        OpType.DELETE: delete_task,
    },
    EntityTypes.RUN: {
        OpType.NEW: new_run,
        OpType.IMPORT: import_run,
        OpType.LOAD: load_run,
        OpType.UPDATE: update_run,
        OpType.GET: get_run,
        OpType.LIST: list_runs,
        OpType.DELETE: delete_run,
    },
    EntityTypes.TRIGGER: {
        OpType.NEW: new_trigger,
        OpType.IMPORT: import_trigger,
        OpType.LOAD: load_trigger,
        OpType.GET: get_trigger,
        OpType.LIST: list_triggers,
        OpType.UPDATE: update_trigger,
        OpType.DELETE: delete_trigger,
    },
    EntityTypes.SECRET: {
        OpType.NEW: new_secret,
        OpType.IMPORT: import_secret,
        OpType.LOAD: load_secret,
        OpType.GET: get_secret,
        OpType.LIST: list_secrets,
        OpType.UPDATE: update_secret,
        OpType.DELETE: delete_secret,
    },
    EntityTypes.CONTAINERIMAGE: {
        OpType.NEW: new_containerimage,
        OpType.IMPORT: import_containerimage,
        OpType.LOAD: load_containerimage,
        OpType.GET: get_containerimage,
        OpType.GET_VERSIONS: get_containerimage_versions,
        OpType.LIST: list_containerimages,
        OpType.UPDATE: update_containerimage,
        OpType.DELETE: delete_containerimage,
    },
}
