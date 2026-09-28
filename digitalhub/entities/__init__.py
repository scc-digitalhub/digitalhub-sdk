# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

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


def _plugins(
    functions: tuple[object, ...],
) -> tuple[CrudPlugin, ...]:
    return tuple(
        CrudPlugin(
            function,
            project_bound="generic" not in function.__name__,
            validate_entity_project=function.__name__.startswith("update_"),
            inject_context=function.__name__.startswith("import_"),
        )
        for function in functions
    )


crud_plugins: tuple[CrudPlugin, ...] = (
    *_plugins(
        (
            new_artifact,
            log_artifact,
            log_generic_artifact,
            register_artifact,
            register_generic_artifact,
            get_artifact,
            get_artifact_versions,
            list_artifacts,
            import_artifact,
            load_artifact,
            update_artifact,
            delete_artifact,
        ),
    ),
    *_plugins(
        (
            new_containerimage,
            get_containerimage,
            get_containerimage_versions,
            list_containerimages,
            import_containerimage,
            load_containerimage,
            update_containerimage,
            delete_containerimage,
        ),
    ),
    *_plugins(
        (
            new_dataitem,
            log_generic_dataitem,
            log_dataitem,
            log_table,
            log_croissant,
            register_generic_dataitem,
            register_dataitem,
            register_table,
            register_croissant,
            get_dataitem,
            get_dataitem_versions,
            list_dataitems,
            import_dataitem,
            load_dataitem,
            update_dataitem,
            delete_dataitem,
        ),
    ),
    *_plugins(
        (
            new_function,
            get_function,
            get_function_versions,
            list_functions,
            import_function,
            load_function,
            update_function,
            delete_function,
        ),
    ),
    *_plugins(
        (
            new_model,
            log_generic_model,
            log_model,
            register_generic_model,
            register_model,
            get_model,
            get_model_versions,
            list_models,
            import_model,
            load_model,
            update_model,
            delete_model,
        ),
    ),
    *_plugins(
        (
            new_run,
            get_run,
            list_runs,
            import_run,
            load_run,
            update_run,
            delete_run,
        ),
    ),
    *_plugins(
        (
            new_secret,
            get_secret,
            list_secrets,
            import_secret,
            load_secret,
            update_secret,
            delete_secret,
        ),
    ),
    *_plugins(
        (
            new_task,
            get_task,
            list_tasks,
            import_task,
            load_task,
            update_task,
            delete_task,
        ),
    ),
    *_plugins(
        (
            new_trigger,
            get_trigger,
            list_triggers,
            import_trigger,
            load_trigger,
            update_trigger,
            delete_trigger,
        ),
    ),
    *_plugins(
        (
            new_workflow,
            get_workflow,
            get_workflow_versions,
            list_workflows,
            import_workflow,
            load_workflow,
            update_workflow,
            delete_workflow,
        ),
    ),
)
