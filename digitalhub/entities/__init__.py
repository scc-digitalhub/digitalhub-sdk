# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from digitalhub.entities.artifact._base.crud import new_artifact
from digitalhub.entities.artifact.artifact.crud import log_artifact, register_artifact
from digitalhub.entities.artifact.crud import (
    delete_artifact,
    get_artifact,
    get_artifact_versions,
    import_artifact,
    list_artifacts,
    load_artifact,
    update_artifact,
)
from digitalhub.entities.artifact.generic.crud import log_generic_artifact, register_generic_artifact
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
from digitalhub.entities.dataitem._base.crud import new_dataitem
from digitalhub.entities.dataitem.croissant.crud import log_croissant, register_croissant
from digitalhub.entities.dataitem.crud import (
    delete_dataitem,
    get_dataitem,
    get_dataitem_versions,
    import_dataitem,
    list_dataitems,
    load_dataitem,
    update_dataitem,
)
from digitalhub.entities.dataitem.dataitem.crud import log_dataitem, register_dataitem
from digitalhub.entities.dataitem.generic.crud import log_generic_dataitem, register_generic_dataitem
from digitalhub.entities.dataitem.table.crud import log_table, register_table
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
from digitalhub.entities.model._base.crud import new_model
from digitalhub.entities.model.crud import (
    delete_model,
    get_model,
    get_model_versions,
    import_model,
    list_models,
    load_model,
    update_model,
)
from digitalhub.entities.model.generic.crud import log_generic_model, register_generic_model
from digitalhub.entities.model.model.crud import log_model, register_model
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
from digitalhub.factory.plugins import CrudPlugin

# Each shortcut declares its project behaviour explicitly, so renaming a
# function never changes it. ``CrudPlugin(f)`` is bound to the project and
# refreshes it after the call.


def _read(function: Callable[..., Any]) -> CrudPlugin:
    """Bound to the project; reading leaves the project as it is."""
    return CrudPlugin(function, refresh_project=False)


def _update(function: Callable[..., Any]) -> CrudPlugin:
    """Bound to the project; the entity must belong to it."""
    return CrudPlugin(function, validate_entity_project=True)


def _import(function: Callable[..., Any]) -> CrudPlugin:
    """Bound to the project; the project context replaces the target project."""
    return CrudPlugin(function, inject_context=True)


def _unbound(function: Callable[..., Any]) -> CrudPlugin:
    """Not exposed as a project method."""
    return CrudPlugin(function, project_bound=False)


crud_plugins: tuple[CrudPlugin, ...] = (
    # Artifact
    CrudPlugin(new_artifact),
    CrudPlugin(log_artifact),
    _unbound(log_generic_artifact),
    CrudPlugin(register_artifact),
    _unbound(register_generic_artifact),
    _read(get_artifact),
    _read(get_artifact_versions),
    _read(list_artifacts),
    _import(import_artifact),
    CrudPlugin(load_artifact),
    _update(update_artifact),
    CrudPlugin(delete_artifact),
    # Container image
    CrudPlugin(new_containerimage),
    _read(get_containerimage),
    _read(get_containerimage_versions),
    _read(list_containerimages),
    _import(import_containerimage),
    CrudPlugin(load_containerimage),
    _update(update_containerimage),
    CrudPlugin(delete_containerimage),
    # Dataitem
    CrudPlugin(new_dataitem),
    _unbound(log_generic_dataitem),
    CrudPlugin(log_dataitem),
    CrudPlugin(log_table),
    CrudPlugin(log_croissant),
    _unbound(register_generic_dataitem),
    CrudPlugin(register_dataitem),
    CrudPlugin(register_table),
    CrudPlugin(register_croissant),
    _read(get_dataitem),
    _read(get_dataitem_versions),
    _read(list_dataitems),
    _import(import_dataitem),
    CrudPlugin(load_dataitem),
    _update(update_dataitem),
    CrudPlugin(delete_dataitem),
    # Function
    CrudPlugin(new_function),
    _read(get_function),
    _read(get_function_versions),
    _read(list_functions),
    _import(import_function),
    CrudPlugin(load_function),
    _update(update_function),
    CrudPlugin(delete_function),
    # Model
    CrudPlugin(new_model),
    _unbound(log_generic_model),
    CrudPlugin(log_model),
    _unbound(register_generic_model),
    CrudPlugin(register_model),
    _read(get_model),
    _read(get_model_versions),
    _read(list_models),
    _import(import_model),
    CrudPlugin(load_model),
    _update(update_model),
    CrudPlugin(delete_model),
    # Run
    CrudPlugin(new_run),
    _read(get_run),
    _read(list_runs),
    _import(import_run),
    CrudPlugin(load_run),
    _update(update_run),
    CrudPlugin(delete_run),
    # Secret
    CrudPlugin(new_secret),
    _read(get_secret),
    _read(list_secrets),
    _import(import_secret),
    CrudPlugin(load_secret),
    _update(update_secret),
    CrudPlugin(delete_secret),
    # Task
    CrudPlugin(new_task),
    _read(get_task),
    _read(list_tasks),
    _import(import_task),
    CrudPlugin(load_task),
    _update(update_task),
    CrudPlugin(delete_task),
    # Trigger
    CrudPlugin(new_trigger),
    _read(get_trigger),
    _read(list_triggers),
    _import(import_trigger),
    CrudPlugin(load_trigger),
    _update(update_trigger),
    CrudPlugin(delete_trigger),
    # Workflow
    CrudPlugin(new_workflow),
    _read(get_workflow),
    _read(get_workflow_versions),
    _read(list_workflows),
    _import(import_workflow),
    CrudPlugin(load_workflow),
    _update(update_workflow),
    CrudPlugin(delete_workflow),
)
