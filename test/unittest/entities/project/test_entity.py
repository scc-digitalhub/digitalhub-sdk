import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.entities.project._base.entity import Project
from digitalhub.utils.exceptions import EntityError


def _project_with_reordered_entity_types() -> Project:
    project = object.__new__(Project)
    project.name = "project"
    project._get_entity_types = Mock(return_value=["functions", "artifacts"])
    project._is_embedded = Mock(return_value=False)
    return project


def _project_entities() -> dict:
    return {
        "spec": {
            "functions": [{"metadata": {"ref": "local://function.yaml"}}],
            "artifacts": [{"metadata": {"ref": "local://artifact.yaml"}}],
        }
    }


def test_import_entities_selects_processor_independently_of_entity_type_order(monkeypatch) -> None:
    project = _project_with_reordered_entity_types()
    method_module = importlib.import_module(Project._import_entities.__module__)
    monkeypatch.setattr(method_module, "has_local_scheme", Mock(return_value=True))
    context_import = Mock()
    executable_import = Mock()
    monkeypatch.setattr(method_module.crud_processor, "import_context_entity", context_import)
    monkeypatch.setattr(method_module.executable_processor, "import_executable_entity", executable_import)

    project._import_entities(_project_entities(), reset_id=True)

    context_import.assert_called_once_with(file="local://artifact.yaml", reset_id=True, context="project")
    executable_import.assert_called_once_with(file="local://function.yaml", reset_id=True, context="project")


def test_load_entities_selects_processor_independently_of_entity_type_order(monkeypatch) -> None:
    project = _project_with_reordered_entity_types()
    method_module = importlib.import_module(Project._load_entities.__module__)
    monkeypatch.setattr(method_module, "has_local_scheme", Mock(return_value=True))
    context_load = Mock()
    executable_load = Mock()
    monkeypatch.setattr(method_module.crud_processor, "load_context_entity", context_load)
    monkeypatch.setattr(method_module.executable_processor, "load_executable_entity", executable_load)

    project._load_entities(_project_entities())

    context_load.assert_called_once_with("local://artifact.yaml")
    executable_load.assert_called_once_with("local://function.yaml")


@pytest.mark.parametrize(
    ("method_name", "manager_name"),
    [
        ("load_artifact", "artifact"),
        ("load_dataitem", "dataitem"),
        ("load_model", "model"),
        ("load_function", "function"),
        ("load_workflow", "workflow"),
        ("load_task", "task"),
        ("load_run", "run"),
        ("load_trigger", "trigger"),
        ("load_secret", "secret"),
    ],
)
def test_load_entity_delegates_to_crud_manager(method_name: str, manager_name: str) -> None:
    loaded = object()
    manager = Mock()
    manager.load.return_value = loaded
    project = object.__new__(Project)
    project.crud = SimpleNamespace(**{manager_name: manager})
    project.refresh = Mock()

    result = getattr(project, method_name)("entity.yaml")

    assert result is loaded
    manager.load.assert_called_once_with("entity.yaml")
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "manager_method", "extra_kwargs"),
    [
        ("register_artifact", "artifact", "register_artifact", {"src_path": None}),
        ("register_generic_artifact", "artifact", "register", {"kind": "custom-artifact"}),
        ("register_dataitem", "dataitem", "register_dataitem", {}),
        ("register_generic_dataitem", "dataitem", "register", {"kind": "custom-dataitem"}),
        ("register_table", "dataitem", "register_table", {"schema": None}),
        ("register_croissant", "dataitem", "register_croissant", {}),
        (
            "register_model",
            "model",
            "register_model",
            {"framework": None, "algorithm": None, "parameters": None},
        ),
        ("register_generic_model", "model", "register", {"kind": "custom-model"}),
        (
            "register_mlflow",
            "model",
            "register_mlflow",
            {
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "flavor": None,
                "model_config": None,
                "input_datasets": None,
                "signature": None,
            },
        ),
        (
            "register_huggingface",
            "model",
            "register_huggingface",
            {
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "base_model": None,
                "model_id": None,
                "model_revision": None,
            },
        ),
        (
            "register_sklearn",
            "model",
            "register_sklearn",
            {"framework": None, "algorithm": None, "parameters": None},
        ),
        (
            "register_tvm_ir",
            "model",
            "register_tvm_ir",
            {
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "entry": None,
                "inputs": None,
                "outputs": None,
                "source_format": None,
                "keep_params_in_input": None,
                "sanitize_input_names": None,
            },
        ),
        (
            "register_tvm_so",
            "model",
            "register_tvm_so",
            {
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "entry": None,
                "inputs": None,
                "outputs": None,
                "target": None,
                "opt_level": None,
                "manifest": None,
            },
        ),
    ],
)
def test_register_entity_delegates_to_crud_manager(
    method_name: str,
    manager_name: str,
    manager_method: str,
    extra_kwargs: dict,
) -> None:
    registered = object()
    manager = Mock()
    getattr(manager, manager_method).return_value = registered
    project = object.__new__(Project)
    project.crud = SimpleNamespace(**{manager_name: manager})
    project.refresh = Mock()

    result = getattr(project, method_name)(
        source="s3://bucket/path/model.bin",
        name="model",
        **extra_kwargs,
    )

    assert result is registered
    getattr(manager, manager_method).assert_called_once_with(
        source="s3://bucket/path/model.bin",
        name="model",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
        **extra_kwargs,
    )
    project.refresh.assert_called_once_with()


def _project_with_manager(manager_name: str) -> tuple[Project, Mock]:
    project = object.__new__(Project)
    manager = Mock()
    project.crud = SimpleNamespace(**{manager_name: manager})
    project.refresh = Mock()
    return project, manager


@pytest.mark.parametrize(
    ("property_name", "manager_name"),
    [
        ("functions", "function"),
        ("workflows", "workflow"),
        ("artifacts", "artifact"),
        ("dataitems", "dataitem"),
        ("models", "model"),
    ],
)
def test_project_entity_properties_delegate_to_crud_manager(property_name: str, manager_name: str) -> None:
    listed = object()
    project, manager = _project_with_manager(manager_name)
    manager.list.return_value = listed

    result = getattr(project, property_name)

    assert result is listed
    manager.list.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "manager_method", "kwargs"),
    [
        (
            "new_artifact",
            "artifact",
            "new",
            {
                "name": "artifact",
                "kind": "artifact",
                "uuid": "artifact-id",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "path": "artifact.bin",
                "extensions": [{"key": "value"}],
                "custom": "value",
            },
        ),
        (
            "new_dataitem",
            "dataitem",
            "new",
            {
                "name": "dataitem",
                "kind": "dataitem",
                "uuid": "dataitem-id",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "path": "data.csv",
                "extensions": [{"key": "value"}],
                "custom": "value",
            },
        ),
        (
            "new_model",
            "model",
            "new",
            {
                "name": "model",
                "kind": "model",
                "uuid": "model-id",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "path": "model.bin",
                "extensions": [{"key": "value"}],
                "custom": "value",
            },
        ),
        (
            "new_function",
            "function",
            "new",
            {
                "name": "function",
                "kind": "function",
                "uuid": "function-id",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "custom": "value",
            },
        ),
        (
            "new_workflow",
            "workflow",
            "new",
            {
                "name": "workflow",
                "kind": "workflow",
                "uuid": "workflow-id",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "custom": "value",
            },
        ),
        (
            "new_task",
            "task",
            "new",
            {
                "kind": "task",
                "name": "task",
                "uuid": "task-id",
                "labels": ["label"],
                "function": "function",
                "workflow": "workflow",
                "custom": "value",
            },
        ),
        (
            "new_run",
            "run",
            "new",
            {
                "kind": "run",
                "name": "run",
                "uuid": "run-id",
                "labels": ["label"],
                "task": "task",
                "custom": "value",
            },
        ),
        (
            "new_trigger",
            "trigger",
            "new",
            {
                "name": "trigger",
                "kind": "trigger",
                "task": "task",
                "function": "function",
                "workflow": "workflow",
                "uuid": "trigger-id",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "template": {"key": "value"},
                "custom": "value",
            },
        ),
        (
            "new_secret",
            "secret",
            "new",
            {
                "name": "secret",
                "uuid": "secret-id",
                "description": "description",
                "labels": ["label"],
                "embedded": True,
                "secret_value": "value",
                "custom": "value",
            },
        ),
        (
            "new_containerimage",
            "containerimage",
            "new",
            {
                "name": "image",
                "image": "registry/image:tag",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
    ],
)
def test_new_entity_delegates_to_crud_manager(
    method_name: str,
    manager_name: str,
    manager_method: str,
    kwargs: dict,
) -> None:
    created = object()
    project, manager = _project_with_manager(manager_name)
    getattr(manager, manager_method).return_value = created

    result = getattr(project, method_name)(**kwargs)

    assert result is created
    getattr(manager, manager_method).assert_called_once_with(**kwargs)
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "manager_method", "kwargs"),
    [
        (
            "log_artifact",
            "artifact",
            "log_artifact",
            {
                "source": "artifact.bin",
                "name": "artifact",
                "drop_existing": True,
                "path": "s3://bucket/artifact.bin",
                "src_path": None,
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
        (
            "log_generic_artifact",
            "artifact",
            "log",
            {
                "kind": "custom-artifact",
                "source": "artifact.bin",
                "name": "artifact",
                "drop_existing": True,
                "path": "s3://bucket/artifact.bin",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
        (
            "log_dataitem",
            "dataitem",
            "log_dataitem",
            {
                "source": "data.csv",
                "name": "dataitem",
                "drop_existing": True,
                "path": "s3://bucket/data.csv",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
        (
            "log_generic_dataitem",
            "dataitem",
            "log",
            {
                "kind": "custom-dataitem",
                "source": "data.csv",
                "name": "dataitem",
                "drop_existing": True,
                "path": "s3://bucket/data.csv",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
        (
            "log_table",
            "dataitem",
            "log_table",
            {
                "name": "table",
                "source": "table.csv",
                "data": object(),
                "sql": "select * from table",
                "drop_existing": True,
                "path": "s3://bucket/table.csv",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "file_format": "csv",
                "read_df_params": {"header": 0},
                "engine": "engine",
                "schema": None,
                "custom": "value",
            },
        ),
        (
            "log_croissant",
            "dataitem",
            "log_croissant",
            {
                "source": "dataset.json",
                "name": "dataset",
                "drop_existing": True,
                "path": "s3://bucket/dataset.json",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
        (
            "log_model",
            "model",
            "log_model",
            {
                "source": "model.bin",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model.bin",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "custom": "value",
            },
        ),
        (
            "log_generic_model",
            "model",
            "log",
            {
                "kind": "custom-model",
                "source": "model.bin",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model.bin",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "custom": "value",
            },
        ),
        (
            "log_mlflow",
            "model",
            "log_mlflow",
            {
                "source": "model",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "flavor": None,
                "model_config": None,
                "input_datasets": None,
                "signature": None,
                "custom": "value",
            },
        ),
        (
            "log_sklearn",
            "model",
            "log_sklearn",
            {
                "source": "model.pkl",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model.pkl",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "custom": "value",
            },
        ),
        (
            "log_huggingface",
            "model",
            "log_huggingface",
            {
                "source": "model",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "base_model": None,
                "model_id": None,
                "model_revision": None,
                "custom": "value",
            },
        ),
        (
            "log_tvm_ir",
            "model",
            "log_tvm_ir",
            {
                "source": "model.json",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model.json",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "entry": None,
                "inputs": None,
                "outputs": None,
                "source_format": None,
                "keep_params_in_input": None,
                "sanitize_input_names": None,
                "custom": "value",
            },
        ),
        (
            "log_tvm_so",
            "model",
            "log_tvm_so",
            {
                "source": "model.so",
                "name": "model",
                "drop_existing": True,
                "path": "s3://bucket/model.so",
                "version": "1",
                "description": "description",
                "labels": ["label"],
                "framework": None,
                "algorithm": None,
                "parameters": None,
                "entry": None,
                "inputs": None,
                "outputs": None,
                "target": None,
                "opt_level": None,
                "manifest": None,
                "custom": "value",
            },
        ),
    ],
)
def test_log_entity_delegates_to_crud_manager(
    method_name: str,
    manager_name: str,
    manager_method: str,
    kwargs: dict,
) -> None:
    logged = object()
    project, manager = _project_with_manager(manager_name)
    getattr(manager, manager_method).return_value = logged

    result = getattr(project, method_name)(**kwargs)

    assert result is logged
    getattr(manager, manager_method).assert_called_once_with(**kwargs)
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "manager_method", "kwargs"),
    [
        ("get_artifact", "artifact", "get", {"identifier": "artifact", "entity_id": "artifact-id"}),
        ("get_dataitem", "dataitem", "get", {"identifier": "dataitem", "entity_id": "dataitem-id"}),
        ("get_model", "model", "get", {"identifier": "model", "entity_id": "model-id"}),
        ("get_function", "function", "get", {"identifier": "function", "entity_id": "function-id"}),
        ("get_workflow", "workflow", "get", {"identifier": "workflow", "entity_id": "workflow-id"}),
        ("get_task", "task", "get", {"identifier": "task"}),
        ("get_run", "run", "get", {"identifier": "run"}),
        ("get_trigger", "trigger", "get", {"identifier": "trigger", "entity_id": "trigger-id"}),
        ("get_secret", "secret", "get", {"identifier": "secret", "entity_id": "secret-id"}),
        (
            "get_containerimage",
            "containerimage",
            "get",
            {"identifier": "image", "entity_id": "image-id"},
        ),
        ("get_artifact_versions", "artifact", "get_versions", {"identifier": "artifact"}),
        ("get_dataitem_versions", "dataitem", "get_versions", {"identifier": "dataitem"}),
        ("get_model_versions", "model", "get_versions", {"identifier": "model"}),
        ("get_function_versions", "function", "get_versions", {"identifier": "function"}),
        ("get_workflow_versions", "workflow", "get_versions", {"identifier": "workflow"}),
        ("get_containerimage_versions", "containerimage", "get_versions", {"identifier": "image"}),
    ],
)
def test_get_entity_delegates_to_crud_manager(
    method_name: str,
    manager_name: str,
    manager_method: str,
    kwargs: dict,
) -> None:
    loaded = object()
    project, manager = _project_with_manager(manager_name)
    getattr(manager, manager_method).return_value = loaded

    result = getattr(project, method_name)(**kwargs)

    assert result is loaded
    getattr(manager, manager_method).assert_called_once_with(**kwargs)
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "manager_method", "spec_kwargs"),
    [
        ("log_artifact", "artifact", "log_artifact", {"src_path": "source.txt"}),
        ("register_artifact", "artifact", "register_artifact", {"src_path": "source.txt"}),
        ("log_table", "dataitem", "log_table", {"schema": {"columns": []}}),
        ("register_table", "dataitem", "register_table", {"schema": {"columns": []}}),
        (
            "log_model",
            "model",
            "log_model",
            {"framework": "pytorch", "algorithm": "resnet", "parameters": {"epochs": 3}},
        ),
        (
            "register_model",
            "model",
            "register_model",
            {"framework": "pytorch", "algorithm": "resnet", "parameters": {"epochs": 3}},
        ),
        (
            "log_sklearn",
            "model",
            "log_sklearn",
            {"framework": "sklearn", "algorithm": "random-forest", "parameters": {"trees": 10}},
        ),
        (
            "register_sklearn",
            "model",
            "register_sklearn",
            {"framework": "sklearn", "algorithm": "random-forest", "parameters": {"trees": 10}},
        ),
        (
            "log_mlflow",
            "model",
            "log_mlflow",
            {
                "framework": "pytorch",
                "algorithm": "resnet",
                "parameters": {"epochs": 3},
                "flavor": "pytorch",
                "model_config": {"device": "cpu"},
                "input_datasets": [object()],
                "signature": object(),
            },
        ),
        (
            "register_mlflow",
            "model",
            "register_mlflow",
            {
                "framework": "pytorch",
                "algorithm": "resnet",
                "parameters": {"epochs": 3},
                "flavor": "pytorch",
                "model_config": {"device": "cpu"},
                "input_datasets": [object()],
                "signature": object(),
            },
        ),
        (
            "log_huggingface",
            "model",
            "log_huggingface",
            {
                "framework": "transformers",
                "algorithm": "bert",
                "parameters": {"epochs": 3},
                "base_model": "bert-base",
                "model_id": "org/model",
                "model_revision": "main",
            },
        ),
        (
            "register_huggingface",
            "model",
            "register_huggingface",
            {
                "framework": "transformers",
                "algorithm": "bert",
                "parameters": {"epochs": 3},
                "base_model": "bert-base",
                "model_id": "org/model",
                "model_revision": "main",
            },
        ),
        (
            "log_tvm_ir",
            "model",
            "log_tvm_ir",
            {
                "framework": "tvm",
                "algorithm": "relax",
                "parameters": {"opt": 2},
                "entry": "main",
                "inputs": [{"name": "input"}],
                "outputs": [{"name": "output"}],
                "source_format": "onnx",
                "keep_params_in_input": True,
                "sanitize_input_names": False,
            },
        ),
        (
            "register_tvm_ir",
            "model",
            "register_tvm_ir",
            {
                "framework": "tvm",
                "algorithm": "relax",
                "parameters": {"opt": 2},
                "entry": "main",
                "inputs": [{"name": "input"}],
                "outputs": [{"name": "output"}],
                "source_format": "onnx",
                "keep_params_in_input": True,
                "sanitize_input_names": False,
            },
        ),
        (
            "log_tvm_so",
            "model",
            "log_tvm_so",
            {
                "framework": "tvm",
                "algorithm": "relax",
                "parameters": {"opt": 2},
                "entry": "main",
                "inputs": [{"name": "input"}],
                "outputs": [{"name": "output"}],
                "target": "llvm",
                "opt_level": 3,
                "manifest": {"version": 1},
            },
        ),
        (
            "register_tvm_so",
            "model",
            "register_tvm_so",
            {
                "framework": "tvm",
                "algorithm": "relax",
                "parameters": {"opt": 2},
                "entry": "main",
                "inputs": [{"name": "input"}],
                "outputs": [{"name": "output"}],
                "target": "llvm",
                "opt_level": 3,
                "manifest": {"version": 1},
            },
        ),
    ],
)
def test_kind_aware_fields_are_forwarded_to_crud_manager(
    method_name: str,
    manager_name: str,
    manager_method: str,
    spec_kwargs: dict,
) -> None:
    result = object()
    project, manager = _project_with_manager(manager_name)
    getattr(manager, manager_method).return_value = result

    assert getattr(project, method_name)(source="model.bin", **spec_kwargs) is result

    forwarded_kwargs = getattr(manager, manager_method).call_args.kwargs
    assert {key: forwarded_kwargs[key] for key in spec_kwargs} == spec_kwargs


@pytest.mark.parametrize(
    ("method_name", "manager_name", "kwargs"),
    [
        (
            "list_artifacts",
            "artifact",
            {
                "q": "query",
                "name": "artifact",
                "kind": "artifact",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "list_dataitems",
            "dataitem",
            {
                "q": "query",
                "name": "dataitem",
                "kind": "dataitem",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "list_models",
            "model",
            {
                "q": "query",
                "name": "model",
                "kind": "model",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "list_functions",
            "function",
            {
                "q": "query",
                "name": "function",
                "kind": "function",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "list_workflows",
            "workflow",
            {
                "q": "query",
                "name": "workflow",
                "kind": "workflow",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "list_tasks",
            "task",
            {
                "q": "query",
                "name": "task",
                "kind": "task",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "function": "function",
                "workflow": "workflow",
            },
        ),
        (
            "list_runs",
            "run",
            {
                "q": "query",
                "name": "run",
                "kind": "run",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "function": "function",
                "workflow": "workflow",
                "task": "task",
                "action": "action",
            },
        ),
        (
            "list_triggers",
            "trigger",
            {
                "q": "query",
                "name": "trigger",
                "kind": "trigger",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
                "task": "task",
            },
        ),
        ("list_secrets", "secret", {}),
        (
            "list_containerimages",
            "containerimage",
            {
                "q": "query",
                "name": "image",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
            },
        ),
    ],
)
def test_list_entities_delegates_to_crud_manager(method_name: str, manager_name: str, kwargs: dict) -> None:
    listed = object()
    project, manager = _project_with_manager(manager_name)
    manager.list.return_value = listed

    result = getattr(project, method_name)(**kwargs)

    assert result is listed
    manager.list.assert_called_once_with(**kwargs)
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "kwargs"),
    [
        ("import_artifact", "artifact", {"file": "artifact.yaml", "key": "artifact", "reset_id": False}),
        ("import_dataitem", "dataitem", {"file": "dataitem.yaml", "key": "dataitem", "reset_id": False}),
        ("import_model", "model", {"file": "model.yaml", "key": "model", "reset_id": False}),
        ("import_function", "function", {"file": "function.yaml", "key": "function", "reset_id": False}),
        ("import_workflow", "workflow", {"file": "workflow.yaml", "key": "workflow", "reset_id": False}),
        ("import_task", "task", {"file": "task.yaml", "key": "task", "reset_id": False}),
        ("import_run", "run", {"file": "run.yaml", "key": "run", "reset_id": False}),
        ("import_trigger", "trigger", {"file": "trigger.yaml", "key": "trigger", "reset_id": False}),
        ("import_secret", "secret", {"file": "secret.yaml", "key": "secret", "reset_id": False}),
        (
            "import_containerimage",
            "containerimage",
            {"file": "image.yaml", "key": "image", "reset_id": False},
        ),
    ],
)
def test_import_entities_delegate_to_crud_manager(method_name: str, manager_name: str, kwargs: dict) -> None:
    imported = object()
    project, manager = _project_with_manager(manager_name)
    manager.import_entity.return_value = imported

    result = getattr(project, method_name)(**kwargs)

    assert result is imported
    manager.import_entity.assert_called_once_with(**kwargs)
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name"),
    [
        ("update_artifact", "artifact"),
        ("update_dataitem", "dataitem"),
        ("update_model", "model"),
        ("update_function", "function"),
        ("update_workflow", "workflow"),
        ("update_task", "task"),
        ("update_run", "run"),
        ("update_trigger", "trigger"),
        ("update_secret", "secret"),
        ("update_containerimage", "containerimage"),
    ],
)
def test_update_entity_delegates_to_crud_manager(method_name: str, manager_name: str) -> None:
    updated = object()
    entity = object()
    project, manager = _project_with_manager(manager_name)
    manager.update.return_value = updated

    result = getattr(project, method_name)(entity)

    assert result is updated
    manager.update.assert_called_once_with(entity)
    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(
    ("method_name", "manager_name", "kwargs"),
    [
        (
            "delete_artifact",
            "artifact",
            {"identifier": "artifact", "entity_id": "artifact-id", "delete_all_versions": True, "cascade": False},
        ),
        (
            "delete_dataitem",
            "dataitem",
            {"identifier": "dataitem", "entity_id": "dataitem-id", "delete_all_versions": True, "cascade": False},
        ),
        (
            "delete_model",
            "model",
            {"identifier": "model", "entity_id": "model-id", "delete_all_versions": True, "cascade": False},
        ),
        (
            "delete_function",
            "function",
            {"identifier": "function", "entity_id": "function-id", "delete_all_versions": True, "cascade": False},
        ),
        (
            "delete_workflow",
            "workflow",
            {"identifier": "workflow", "entity_id": "workflow-id", "delete_all_versions": True, "cascade": False},
        ),
        (
            "delete_task",
            "task",
            {"identifier": "task", "entity_id": "task-id", "cascade": False},
        ),
        ("delete_run", "run", {"identifier": "run", "entity_id": "run-id"}),
        ("delete_trigger", "trigger", {"identifier": "trigger", "entity_id": "trigger-id"}),
        (
            "delete_secret",
            "secret",
            {"identifier": "secret", "entity_id": "secret-id", "delete_all_versions": True},
        ),
        (
            "delete_containerimage",
            "containerimage",
            {"identifier": "image", "entity_id": "image-id", "delete_all_versions": True, "cascade": False},
        ),
    ],
)
def test_delete_entity_delegates_to_crud_manager(method_name: str, manager_name: str, kwargs: dict) -> None:
    project, manager = _project_with_manager(manager_name)

    result = getattr(project, method_name)(**kwargs)

    assert result is None
    manager.delete.assert_called_once_with(**kwargs)
    project.refresh.assert_called_once_with()


def test_auto_refresh_does_not_refresh_when_operation_fails() -> None:
    project, manager = _project_with_manager("artifact")
    manager.new.side_effect = RuntimeError("backend failure")

    with pytest.raises(RuntimeError, match="backend failure"):
        project.new_artifact(name="artifact", kind="artifact")

    project.refresh.assert_not_called()


def test_save_creates_project_and_updates_attributes(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    created = object()
    create_project = Mock(return_value=created)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_crud_processor.create_project_entity",
        create_project,
    )
    project._update_attributes = Mock()

    result = project.save()

    assert result is project
    create_project.assert_called_once_with(_entity=project)
    project._update_attributes.assert_called_once_with(created)


def test_save_updates_project(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    project.to_dict = Mock(return_value={"name": "project"})
    updated = object()
    update_project = Mock(return_value=updated)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_crud_processor.update_project_entity",
        update_project,
    )
    project._update_attributes = Mock()

    result = project.save(update=True)

    assert result is project
    update_project.assert_called_once_with(
        entity_type=project.ENTITY_TYPE,
        entity_name="project",
        entity_dict={"name": "project"},
    )
    project._update_attributes.assert_called_once_with(updated)


def test_refresh_reads_project_and_updates_attributes(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    refreshed = object()
    read_project = Mock(return_value=refreshed)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_crud_processor.read_project_entity",
        read_project,
    )
    project._update_attributes = Mock()

    result = project.refresh()

    assert result is project
    read_project.assert_called_once_with(entity_type=project.ENTITY_TYPE, entity_name="project")
    project._update_attributes.assert_called_once_with(refreshed)


def test_export_writes_references_for_non_embedded_entities(monkeypatch, tmp_path) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    project.spec = SimpleNamespace(source=str(tmp_path))
    project._refresh_to_dict = Mock(
        return_value={"spec": {"artifacts": [{"key": "artifact-key", "metadata": {}}]}}
    )
    artifact = SimpleNamespace(export=Mock(return_value="artifact.yaml"))
    read_entity = Mock(return_value=artifact)
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.crud_processor.read_context_entity",
        read_entity,
    )
    write_yaml = Mock()
    monkeypatch.setattr("digitalhub.entities.project._base.entity.write_yaml", write_yaml)

    result = project.export()

    expected_path = tmp_path / "projects-project.yaml"
    assert result == str(expected_path)
    project._refresh_to_dict.assert_called_once_with()
    read_entity.assert_called_once_with("artifact-key")
    artifact.export.assert_called_once_with()
    write_yaml.assert_called_once_with(
        expected_path,
        {"spec": {"artifacts": [{"key": "artifact-key", "metadata": {"ref": "artifact.yaml"}}]}},
    )


def test_export_skips_embedded_entities(monkeypatch, tmp_path) -> None:
    project = object.__new__(Project)
    project.name = "project"
    project.ENTITY_TYPE = "project"
    project.spec = SimpleNamespace(source=str(tmp_path))
    project._refresh_to_dict = Mock(
        return_value={
            "spec": {
                "artifacts": [
                    {
                        "key": "artifact-key",
                        "metadata": {"embedded": True},
                        "spec": {"path": "artifact.bin"},
                    }
                ]
            }
        }
    )
    read_entity = Mock()
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.crud_processor.read_context_entity",
        read_entity,
    )
    write_yaml = Mock()
    monkeypatch.setattr("digitalhub.entities.project._base.entity.write_yaml", write_yaml)

    project.export()

    read_entity.assert_not_called()
    write_yaml.assert_called_once_with(
        tmp_path / "projects-project.yaml",
        {
            "spec": {
                "artifacts": [
                    {
                        "key": "artifact-key",
                        "metadata": {"embedded": True},
                        "spec": {"path": "artifact.bin"},
                    }
                ]
            }
        },
    )


def test_search_entity_delegates_to_search_processor(monkeypatch) -> None:
    project = object.__new__(Project)
    project.name = "project"
    search = Mock(return_value=([], []))
    monkeypatch.setattr("digitalhub.entities.project._base.entity.search_processor.search_entity", search)

    result = project.search_entity(
        query="query",
        entity_types=["artifacts"],
        name="artifact",
        kind="artifact",
        created="created",
        updated="updated",
        description="description",
        labels=["label"],
        custom="value",
    )

    assert result == ([], [])
    search.assert_called_once_with(
        "project",
        query="query",
        entity_types=["artifacts"],
        name="artifact",
        kind="artifact",
        created="created",
        updated="updated",
        description="description",
        labels=["label"],
        custom="value",
    )


def test_run_refreshes_selects_workflow_and_forwards_kwargs() -> None:
    project = object.__new__(Project)
    project.spec = SimpleNamespace(workflows=[{"name": "main", "key": "workflow-key"}])
    project.refresh = Mock()
    workflow = Mock()
    workflow.run.return_value = "run"
    project.get_workflow = Mock(return_value=workflow)

    result = project.run(workflow="main", parameter="value")

    assert result == "run"
    project.refresh.assert_called_once_with()
    project.get_workflow.assert_called_once_with("workflow-key")
    workflow.run.assert_called_once_with(parameter="value")


def test_run_uses_main_workflow_by_default() -> None:
    project = object.__new__(Project)
    project.spec = SimpleNamespace(workflows=[{"name": "main", "key": "workflow-key"}])
    project.refresh = Mock()
    workflow = Mock()
    project.get_workflow = Mock(return_value=workflow)

    project.run()

    project.get_workflow.assert_called_once_with("workflow-key")
    workflow.run.assert_called_once_with()


def test_run_raises_when_workflow_is_not_found() -> None:
    project = object.__new__(Project)
    project.spec = SimpleNamespace(workflows=[])
    project.refresh = Mock()

    with pytest.raises(EntityError, match="Workflow missing not found"):
        project.run(workflow="missing")

    project.refresh.assert_called_once_with()


@pytest.mark.parametrize(("method_name", "unshare"), [("share", False), ("unshare", True)])
def test_share_operations_delegate_to_special_processor(monkeypatch, method_name: str, unshare: bool) -> None:
    project = object.__new__(Project)
    project.name = "project"
    share_project = Mock()
    monkeypatch.setattr(
        "digitalhub.entities.project._base.entity.base_special_ops_processor.share_project_entity", share_project
    )

    result = getattr(project, method_name)("user")

    assert result is share_project.return_value
    share_project.assert_called_once_with(
        entity_type=project.ENTITY_TYPE,
        entity_name="project",
        user="user",
        unshare=unshare,
    )
