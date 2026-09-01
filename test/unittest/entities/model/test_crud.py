from unittest.mock import Mock

import pytest

import digitalhub.entities.model._base.crud as base_crud
import digitalhub.entities.model.crud as context_crud
import digitalhub.entities.model.generic.crud as generic_crud
import digitalhub.entities.model.huggingface.crud as huggingface_crud
import digitalhub.entities.model.mlflow.crud as mlflow_crud
import digitalhub.entities.model.model.crud as model_crud
import digitalhub.entities.model.sklearn.crud as sklearn_crud
import digitalhub.entities.model.tvm_ir.crud as tvm_ir_crud
import digitalhub.entities.model.tvm_so.crud as tvm_so_crud
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes


def test_register_model_delegates_to_base_with_specific_kind(monkeypatch) -> None:
    register_base_model = Mock(return_value="model")
    monkeypatch.setattr(model_crud, "register_base_model", register_base_model)

    result = model_crud.register_model(
        project="my-project",
        source="s3://my-bucket/models/model.bin",
        name="model",
    )

    assert result == "model"
    register_base_model.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/models/model.bin",
        entity_kind=EntityKinds.MODEL_MODEL.value,
        name="model",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_register_generic_model_passes_dynamic_kind(monkeypatch) -> None:
    register_base_model = Mock(return_value="model")
    monkeypatch.setattr(generic_crud, "register_base_model", register_base_model)

    result = generic_crud.register_generic_model(
        project="my-project",
        kind="custom-model",
        source="s3://my-bucket/models/model.bin",
    )

    assert result == "model"
    register_base_model.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/models/model.bin",
        entity_kind="custom-model",
        name=None,
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_register_base_model_passes_source_as_path(monkeypatch) -> None:
    new_model = Mock(return_value="model")
    monkeypatch.setattr(base_crud, "new_model", new_model)

    result = base_crud.register_base_model(
        project="my-project",
        source=["s3://my-bucket/models/model.bin"],
        entity_kind=EntityKinds.MODEL_MODEL.value,
        name="model",
    )

    assert result == "model"
    new_model.assert_called_once_with(
        project="my-project",
        name="model",
        kind=EntityKinds.MODEL_MODEL.value,
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        path="s3://my-bucket/models/model.bin",
        extensions=None,
    )


@pytest.mark.parametrize(
    ("crud_module", "register_name", "entity_kind"),
    [
        (mlflow_crud, "register_mlflow", EntityKinds.MODEL_MLFLOW.value),
        (huggingface_crud, "register_huggingface", EntityKinds.MODEL_HUGGINGFACE.value),
        (sklearn_crud, "register_sklearn", EntityKinds.MODEL_SKLEARN.value),
        (tvm_ir_crud, "register_tvm_ir", EntityKinds.MODEL_TVM_IR.value),
        (tvm_so_crud, "register_tvm_so", EntityKinds.MODEL_TVM_SO.value),
    ],
)
def test_register_model_specialized_delegates_to_base(crud_module, register_name, entity_kind, monkeypatch) -> None:
    register_base_model = Mock(return_value="model")
    monkeypatch.setattr(crud_module, "register_base_model", register_base_model)

    result = getattr(crud_module, register_name)(
        project="my-project",
        source="s3://my-bucket/models/model.bin",
        name="model",
    )

    assert result == "model"
    register_base_model.assert_called_once_with(
        project="my-project",
        source="s3://my-bucket/models/model.bin",
        entity_kind=entity_kind,
        name="model",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_new_model_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="model")
    monkeypatch.setattr(base_crud.crud_processor, "create_context_entity", create_entity)

    result = base_crud.new_model(
        project="my-project",
        name="model",
        kind="custom-model",
        uuid="model-id",
        version="1",
        description="A model",
        labels=["production"],
        embedded=True,
        path="s3://bucket/model.bin",
        extensions=[{"key": "value"}],
        framework="custom",
    )

    assert result == "model"
    create_entity.assert_called_once_with(
        project="my-project",
        name="model",
        kind="custom-model",
        uuid="model-id",
        version="1",
        description="A model",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.MODEL.value,
        path="s3://bucket/model.bin",
        extensions=[{"key": "value"}],
        framework="custom",
    )


def test_log_base_model_validates_source_and_builds_storage_kwargs(monkeypatch) -> None:
    eval_source = Mock()
    build_name = Mock(return_value="inferred-model")
    build_kwargs = Mock(return_value={"path": "s3://bucket/model.bin", "format": "bin"})
    log_entity = Mock(return_value="model")
    monkeypatch.setattr(base_crud, "eval_local_source", eval_source)
    monkeypatch.setattr(base_crud, "build_log_name_from_source", build_name)
    monkeypatch.setattr(base_crud, "build_log_kwargs", build_kwargs)
    monkeypatch.setattr(base_crud.material_processor, "log_material_entity", log_entity)

    source = ["./model.bin"]
    result = base_crud.log_base_model(
        project="my-project",
        kind="custom-model",
        source=source,
        version="1",
        description="A model",
        labels=["production"],
        format="bin",
    )

    assert result == "model"
    eval_source.assert_called_once_with(source)
    build_name.assert_called_once_with(source)
    build_kwargs.assert_called_once_with(
        "my-project",
        "inferred-model",
        entity_type=EntityTypes.MODEL.value,
        source=source,
        path=None,
        format="bin",
    )
    log_entity.assert_called_once_with(
        source=source,
        project="my-project",
        name="inferred-model",
        kind="custom-model",
        drop_existing=False,
        entity_type=EntityTypes.MODEL.value,
        version="1",
        description="A model",
        labels=["production"],
        path="s3://bucket/model.bin",
        format="bin",
    )


def test_log_generic_model_delegates_to_base(monkeypatch) -> None:
    log_base_model = Mock(return_value="model")
    monkeypatch.setattr(generic_crud, "log_base_model", log_base_model)

    result = generic_crud.log_generic_model(
        project="my-project",
        kind="custom-model",
        source="./model.bin",
        name="model",
        drop_existing=True,
        path="s3://bucket/model.bin",
        version="1",
        description="A model",
        labels=["production"],
        format="bin",
    )

    assert result == "model"
    log_base_model.assert_called_once_with(
        project="my-project",
        name="model",
        kind="custom-model",
        source="./model.bin",
        drop_existing=True,
        path="s3://bucket/model.bin",
        version="1",
        description="A model",
        labels=["production"],
        format="bin",
    )


@pytest.mark.parametrize(
    ("crud_module", "log_name", "kind"),
    [
        (model_crud, "log_model", EntityKinds.MODEL_MODEL.value),
        (mlflow_crud, "log_mlflow", EntityKinds.MODEL_MLFLOW.value),
        (huggingface_crud, "log_huggingface", EntityKinds.MODEL_HUGGINGFACE.value),
        (sklearn_crud, "log_sklearn", EntityKinds.MODEL_SKLEARN.value),
        (tvm_ir_crud, "log_tvm_ir", EntityKinds.MODEL_TVM_IR.value),
        (tvm_so_crud, "log_tvm_so", EntityKinds.MODEL_TVM_SO.value),
    ],
)
def test_log_model_specialized_delegates_to_base(crud_module, log_name, kind, monkeypatch) -> None:
    log_base_model = Mock(return_value="model")
    monkeypatch.setattr(crud_module, "log_base_model", log_base_model)

    result = getattr(crud_module, log_name)(
        project="my-project",
        source="./model.bin",
        name="model",
        drop_existing=True,
        path="s3://bucket/model.bin",
        version="1",
        description="A model",
        labels=["production"],
        format="bin",
    )

    assert result == "model"
    log_base_model.assert_called_once_with(
        project="my-project",
        name="model",
        kind=kind,
        source="./model.bin",
        drop_existing=True,
        path="s3://bucket/model.bin",
        version="1",
        description="A model",
        labels=["production"],
        format="bin",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_model",
            "read_context_entity",
            {"identifier": "model-key", "project": "my-project", "entity_id": "model-id"},
            {
                "identifier": "model-key",
                "entity_type": EntityTypes.MODEL.value,
                "project": "my-project",
                "entity_id": "model-id",
            },
        ),
        (
            "get_model_versions",
            "read_context_entity_versions",
            {"identifier": "model", "project": "my-project"},
            {"identifier": "model", "entity_type": EntityTypes.MODEL.value, "project": "my-project"},
        ),
        (
            "list_models",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "model",
                "kind": "custom-model",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.MODEL.value,
                "q": "query",
                "name": "model",
                "kind": "custom-model",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "import_model",
            "import_context_entity",
            {"file": "model.yaml", "key": "model-key", "reset_id": True, "context": "project"},
            {"file": "model.yaml", "key": "model-key", "reset_id": True, "context": "project"},
        ),
        (
            "load_model",
            "load_context_entity",
            {"file": "model.yaml"},
            {"file": "model.yaml"},
        ),
    ],
)
def test_model_read_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="model")
    monkeypatch.setattr(context_crud.crud_processor, processor_name, processor)

    result = getattr(context_crud, function_name)(**kwargs)

    assert result == "model"
    if function_name == "import_model":
        processor.assert_called_once_with(
            expected_kwargs["file"],
            expected_kwargs["key"],
            expected_kwargs["reset_id"],
            expected_kwargs["context"],
        )
    elif function_name == "load_model":
        processor.assert_called_once_with(expected_kwargs["file"])
    else:
        processor.assert_called_once_with(**expected_kwargs)
