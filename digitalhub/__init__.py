from digitalhub_core import (
    delete_artifact,
    delete_function,
    delete_project,
    delete_run,
    delete_secret,
    delete_task,
    delete_workflow,
    get_artifact,
    get_function,
    get_run,
    get_secret,
    get_task,
    get_workflow,
    import_artifact,
    import_function,
    import_run,
    import_secret,
    import_task,
    import_workflow,
    list_artifacts,
    list_functions,
    list_runs,
    list_secrets,
    list_tasks,
    list_workflows,
    new_artifact,
    new_function,
    new_run,
    new_secret,
    new_task,
    new_workflow,
    set_dhub_env,
    set_store,
    update_artifact,
    update_function,
    update_project,
    update_run,
    update_secret,
    update_task,
    update_workflow,
)
from digitalhub_core.registry.import_utils import register_layer_entities, register_runtimes_entities

_PROJECT_IMPORTED = False

if not _PROJECT_IMPORTED:
    try:
        from digitalhub_data import (
            delete_dataitem,
            get_dataitem,
            import_dataitem,
            list_dataitems,
            new_dataitem,
            update_dataitem,
        )
        from digitalhub_ml import (
            delete_model,
            get_model,
            get_or_create_project,
            get_project,
            import_model,
            import_project,
            list_models,
            load_project,
            new_model,
            new_project,
            update_model,
        )

        _PROJECT_IMPORTED = True
    except ImportError:
        ...

if not _PROJECT_IMPORTED:
    try:
        from digitalhub_data import (
            delete_dataitem,
            get_dataitem,
            get_or_create_project,
            get_project,
            import_dataitem,
            import_project,
            list_dataitems,
            load_project,
            new_dataitem,
            new_project,
            update_dataitem,
        )

        _PROJECT_IMPORTED = True
    except ImportError:
        ...

if not _PROJECT_IMPORTED:
    from digitalhub_core import get_or_create_project, get_project, import_project, load_project, new_project


# Register entities into registry
register_layer_entities()
register_runtimes_entities()
