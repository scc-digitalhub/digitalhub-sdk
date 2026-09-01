from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.material.utils as material_utils
import digitalhub.entities.artifact._base.crud as artifact_base_crud
import digitalhub.entities.artifact.artifact.crud as artifact_crud
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
