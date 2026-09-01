from unittest.mock import Mock

import pytest

import digitalhub.entities.model._base.crud as base_crud
import digitalhub.entities.model.generic.crud as generic_crud
import digitalhub.entities.model.huggingface.crud as huggingface_crud
import digitalhub.entities.model.mlflow.crud as mlflow_crud
import digitalhub.entities.model.model.crud as model_crud
import digitalhub.entities.model.sklearn.crud as sklearn_crud
import digitalhub.entities.model.tvm_ir.crud as tvm_ir_crud
import digitalhub.entities.model.tvm_so.crud as tvm_so_crud
from digitalhub.entities._commons.enums import EntityKinds


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
