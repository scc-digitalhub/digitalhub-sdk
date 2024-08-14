import digitalhub

METHODS = [
    "new_artifact",
    "new_function",
    "new_project",
    "new_run",
    "new_secret",
    "new_task",
    "new_workflow",
    "new_dataitem",
    "new_model",
    "get_artifact",
    "get_function",
    "get_project",
    "get_run",
    "get_secret",
    "get_task",
    "get_workflow",
    "get_dataitem",
    "get_model",
    "import_artifact",
    "import_function",
    "import_project",
    "import_run",
    "import_secret",
    "import_task",
    "import_workflow",
    "import_dataitem",
    "import_model",
    "list_artifacts",
    "list_functions",
    "list_runs",
    "list_secrets",
    "list_tasks",
    "list_workflows",
    "list_dataitems",
    "list_models",
    "update_artifact",
    "update_function",
    "update_project",
    "update_run",
    "update_secret",
    "update_task",
    "update_workflow",
    "update_dataitem",
    "update_model",
    "delete_artifact",
    "delete_function",
    "delete_project",
    "delete_run",
    "delete_secret",
    "delete_task",
    "delete_workflow",
    "delete_dataitem",
    "delete_model",
    "set_dhcore_env",
    "set_store",
    "load_project",
    "get_or_create_project",
]


def test_imports():
    for i in METHODS:
        assert hasattr(digitalhub, i)
