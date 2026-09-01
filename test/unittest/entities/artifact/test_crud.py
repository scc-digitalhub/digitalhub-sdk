from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.material.utils as material_utils
import digitalhub.entities.artifact._base.crud as artifact_base_crud
import digitalhub.entities.artifact.artifact.crud as artifact_crud
import digitalhub.entities.artifact.crud as context_crud
import digitalhub.entities.artifact.generic.crud as generic_crud
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes


def test_register_artifact_delegates_to_base_with_specific_kind(monkeypatch) -> None:
    source = "s3://my-bucket/models/my-model.pkl"
    register_base_artifact = Mock(return_value="artifact")
    monkeypatch.setattr(artifact_crud, "register_base_artifact", register_base_artifact)

    result = artifact_crud.register_artifact(
        project="my-project",
        source=source,
        name="my-model",
        description="Registered artifact",
        src_path="s3://my-bucket/incoming/my-model.pkl",
    )

    assert result == "artifact"
    register_base_artifact.assert_called_once_with(
        project="my-project",
        source=source,
        entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        name="my-model",
        uuid=None,
        version=None,
        description="Registered artifact",
        labels=None,
        embedded=False,
        extensions=None,
        src_path="s3://my-bucket/incoming/my-model.pkl",
    )


def test_register_base_artifact_uses_source_as_path_and_infers_name(monkeypatch) -> None:
    source = ["s3://my-bucket/models/my-model.pkl"]
    new_artifact = Mock(return_value="artifact")
    kind_warning = Mock()
    monkeypatch.setattr(artifact_base_crud, "new_artifact", new_artifact)
    monkeypatch.setattr(artifact_base_crud, "kind_warning", kind_warning)
    monkeypatch.setattr(material_utils, "name_warning", Mock())

    result = artifact_base_crud.register_base_artifact(
        project="my-project",
        source=source,
        entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        uuid=None,
        version=None,
        description="Registered artifact",
        labels=None,
        embedded=False,
        extensions=None,
        src_path="s3://my-bucket/incoming/my-model.pkl",
    )

    assert result == "artifact"
    kind_warning.assert_called_once_with(
        requested_kind=None,
        set_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        entity_type=EntityTypes.ARTIFACT.value,
    )
    new_artifact.assert_called_once_with(
        project="my-project",
        name="my-model",
        kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        uuid=None,
        version=None,
        description="Registered artifact",
        labels=None,
        embedded=False,
        path=source[0],
        extensions=None,
        src_path="s3://my-bucket/incoming/my-model.pkl",
    )


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        ("sql://my-db/my-table", "my-table"),
        ("sql://my-db/my-schema/my-table", "my-table"),
    ],
)
def test_build_register_name_uses_sql_table_name(monkeypatch, source, expected_name) -> None:
    name_warning = Mock()
    monkeypatch.setattr(material_utils, "name_warning", name_warning)

    assert (
        material_utils.build_register_name(
            name=None,
            source=source,
            entity_type=EntityTypes.ARTIFACT.value,
            entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        )
        == expected_name
    )
    name_warning.assert_called_once_with(
        inferred_name=expected_name,
        entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
    )


def test_build_log_name_from_source_rejects_invalid_sql_path() -> None:
    with pytest.raises(ValueError, match="Invalid SQL path"):
        material_utils.build_register_name(
            name=None,
            source="sql://my-db/my-schema/my-table/extra",
            entity_type=EntityTypes.ARTIFACT.value,
            entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        )


def test_build_register_name_rejects_multiple_sources_with_name() -> None:
    with pytest.raises(ValueError, match="register_artifact requires a single source path"):
        material_utils.build_register_name(
            name="registered-artifact",
            source=["s3://bucket/one", "s3://bucket/two"],
            entity_type=EntityTypes.ARTIFACT.value,
            entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        )


def test_register_artifact_unwraps_single_source(monkeypatch) -> None:
    register_base_artifact = Mock(return_value="artifact")
    monkeypatch.setattr(artifact_crud, "register_base_artifact", register_base_artifact)

    result = artifact_crud.register_artifact(
        project="my-project",
        source=["sql://my-db/my-schema/my-table"],
        name="registered-table",
    )

    assert result == "artifact"
    register_base_artifact.assert_called_once_with(
        project="my-project",
        source=["sql://my-db/my-schema/my-table"],
        entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        name="registered-table",
        uuid=None,
        version=None,
        description=None,
        labels=None,
        embedded=False,
        extensions=None,
    )


def test_name_warning_logs_inferred_name(monkeypatch) -> None:
    logger = Mock()
    monkeypatch.setattr(material_utils, "logger", logger)

    material_utils.name_warning(
        inferred_name="my-model",
        entity_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
    )

    logger.warning.assert_called_once_with("Name not provided for 'artifact'. Inferred name: 'my-model'.")


def test_new_artifact_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="artifact")
    monkeypatch.setattr(artifact_base_crud.crud_processor, "create_context_entity", create_entity)

    result = artifact_base_crud.new_artifact(
        project="my-project",
        name="artifact",
        kind="custom-artifact",
        uuid="artifact-id",
        version="1",
        description="An artifact",
        labels=["production"],
        embedded=True,
        path="s3://bucket/artifact.bin",
        extensions=[{"key": "value"}],
        format="bin",
    )

    assert result == "artifact"
    create_entity.assert_called_once_with(
        project="my-project",
        name="artifact",
        kind="custom-artifact",
        uuid="artifact-id",
        version="1",
        description="An artifact",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.ARTIFACT.value,
        path="s3://bucket/artifact.bin",
        extensions=[{"key": "value"}],
        format="bin",
    )


def test_log_base_artifact_validates_source_and_builds_storage_kwargs(monkeypatch) -> None:
    eval_source = Mock()
    build_name = Mock(return_value="inferred-artifact")
    build_kwargs = Mock(return_value={"path": "s3://bucket/artifact.bin", "format": "bin"})
    log_entity = Mock(return_value="artifact")
    monkeypatch.setattr(artifact_base_crud, "eval_local_source", eval_source)
    monkeypatch.setattr(artifact_base_crud, "build_log_name_from_source", build_name)
    monkeypatch.setattr(artifact_base_crud, "build_log_kwargs", build_kwargs)
    monkeypatch.setattr(artifact_base_crud.material_processor, "log_material_entity", log_entity)

    source = ["./artifact.bin"]
    result = artifact_base_crud.log_base_artifact(
        project="my-project",
        kind="custom-artifact",
        source=source,
        drop_existing=True,
        path="s3://bucket/artifact.bin",
        version="1",
        description="An artifact",
        labels=["production"],
        format="bin",
    )

    assert result == "artifact"
    eval_source.assert_called_once_with(source)
    build_name.assert_called_once_with(source)
    build_kwargs.assert_called_once_with(
        "my-project",
        "inferred-artifact",
        entity_type=EntityTypes.ARTIFACT.value,
        source=source,
        path="s3://bucket/artifact.bin",
        format="bin",
    )
    log_entity.assert_called_once_with(
        source=source,
        project="my-project",
        name="inferred-artifact",
        kind="custom-artifact",
        drop_existing=True,
        entity_type=EntityTypes.ARTIFACT.value,
        version="1",
        description="An artifact",
        labels=["production"],
        path="s3://bucket/artifact.bin",
        format="bin",
    )


def test_log_generic_artifact_delegates_to_base(monkeypatch) -> None:
    log_base_artifact = Mock(return_value="artifact")
    monkeypatch.setattr(generic_crud, "log_base_artifact", log_base_artifact)

    result = generic_crud.log_generic_artifact(
        project="my-project",
        kind="custom-artifact",
        source="./artifact.bin",
        name="artifact",
        drop_existing=True,
        path="s3://bucket/artifact.bin",
        version="1",
        description="An artifact",
        labels=["production"],
        format="bin",
    )

    assert result == "artifact"
    log_base_artifact.assert_called_once_with(
        project="my-project",
        name="artifact",
        kind="custom-artifact",
        source="./artifact.bin",
        drop_existing=True,
        path="s3://bucket/artifact.bin",
        version="1",
        description="An artifact",
        labels=["production"],
        format="bin",
    )


def test_register_generic_artifact_delegates_to_base(monkeypatch) -> None:
    register_base_artifact = Mock(return_value="artifact")
    monkeypatch.setattr(generic_crud, "register_base_artifact", register_base_artifact)

    result = generic_crud.register_generic_artifact(
        project="my-project",
        kind="custom-artifact",
        source="s3://bucket/artifact.bin",
        name="artifact",
        uuid="artifact-id",
        version="1",
        description="An artifact",
        labels=["production"],
        embedded=True,
        extensions=[{"key": "value"}],
        format="bin",
    )

    assert result == "artifact"
    register_base_artifact.assert_called_once_with(
        project="my-project",
        source="s3://bucket/artifact.bin",
        entity_kind="custom-artifact",
        name="artifact",
        uuid="artifact-id",
        version="1",
        description="An artifact",
        labels=["production"],
        embedded=True,
        extensions=[{"key": "value"}],
        format="bin",
    )


def test_log_artifact_warns_and_delegates_to_base(monkeypatch) -> None:
    kind_warning = Mock()
    log_base_artifact = Mock(return_value="artifact")
    monkeypatch.setattr(artifact_crud, "kind_warning", kind_warning)
    monkeypatch.setattr(artifact_crud, "log_base_artifact", log_base_artifact)

    result = artifact_crud.log_artifact(
        project="my-project",
        source="./artifact.bin",
        name="artifact",
        kind="wrong-kind",
        drop_existing=True,
        path="s3://bucket/artifact.bin",
        version="1",
        description="An artifact",
        labels=["production"],
        format="bin",
    )

    assert result == "artifact"
    kind_warning.assert_called_once_with(
        requested_kind="wrong-kind",
        set_kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        entity_type=EntityTypes.ARTIFACT.value,
    )
    log_base_artifact.assert_called_once_with(
        project="my-project",
        name="artifact",
        kind=EntityKinds.ARTIFACT_ARTIFACT.value,
        source="./artifact.bin",
        drop_existing=True,
        path="s3://bucket/artifact.bin",
        version="1",
        description="An artifact",
        labels=["production"],
        format="bin",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_artifact",
            "read_context_entity",
            {"identifier": "artifact-key", "project": "my-project", "entity_id": "artifact-id"},
            {
                "identifier": "artifact-key",
                "entity_type": EntityTypes.ARTIFACT.value,
                "project": "my-project",
                "entity_id": "artifact-id",
            },
        ),
        (
            "get_artifact_versions",
            "read_context_entity_versions",
            {"identifier": "artifact", "project": "my-project"},
            {"identifier": "artifact", "entity_type": EntityTypes.ARTIFACT.value, "project": "my-project"},
        ),
        (
            "list_artifacts",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "artifact",
                "kind": "custom-artifact",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.ARTIFACT.value,
                "q": "query",
                "name": "artifact",
                "kind": "custom-artifact",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "import_artifact",
            "import_context_entity",
            {"file": "artifact.yaml", "key": "artifact-key", "reset_id": True, "context": "project"},
            None,
        ),
        ("load_artifact", "load_context_entity", {"file": "artifact.yaml"}, None),
        (
            "delete_artifact",
            "delete_context_entity",
            {
                "identifier": "artifact",
                "project": "my-project",
                "entity_id": "artifact-id",
                "delete_all_versions": True,
                "cascade": False,
            },
            {
                "identifier": "artifact",
                "entity_type": EntityTypes.ARTIFACT.value,
                "project": "my-project",
                "entity_id": "artifact-id",
                "delete_all_versions": True,
                "cascade": False,
            },
        ),
    ],
)
def test_artifact_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict | None,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(context_crud.crud_processor, processor_name, processor)

    result = getattr(context_crud, function_name)(**kwargs)

    assert result == "result"
    if function_name == "import_artifact":
        processor.assert_called_once_with(kwargs["file"], kwargs["key"], kwargs["reset_id"], kwargs["context"])
    elif function_name == "load_artifact":
        processor.assert_called_once_with(kwargs["file"])
    else:
        processor.assert_called_once_with(**expected_kwargs)


def test_update_artifact_delegates_entity_fields(monkeypatch) -> None:
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = EntityTypes.ARTIFACT.value
    entity.id = "artifact-id"
    entity.to_dict.return_value = {"metadata": {"name": "artifact"}}
    update_entity = Mock(return_value="artifact")
    monkeypatch.setattr(context_crud.crud_processor, "update_context_entity", update_entity)

    result = context_crud.update_artifact(entity)

    assert result == "artifact"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.ARTIFACT.value,
        entity_id="artifact-id",
        entity_dict={"metadata": {"name": "artifact"}},
    )
