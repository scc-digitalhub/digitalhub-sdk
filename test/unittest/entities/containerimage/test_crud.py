from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities.containerimage.crud as containerimage_crud
from digitalhub.entities._commons.enums import EntityTypes


def test_new_containerimage_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="containerimage")
    monkeypatch.setattr(containerimage_crud.crud_processor, "create_context_entity", create_entity)

    result = containerimage_crud.new_containerimage(
        project="my-project",
        name="api",
        kind="container-image",
        uuid="image-id",
        version="1.2.3",
        description="API image",
        labels=["production"],
        embedded=True,
        image="registry.example.com/api:1.2.3",
        architecture="amd64",
    )

    assert result == "containerimage"
    create_entity.assert_called_once_with(
        project="my-project",
        name="api",
        kind="container-image",
        uuid="image-id",
        version="1.2.3",
        description="API image",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.CONTAINERIMAGE.value,
        image="registry.example.com/api:1.2.3",
        architecture="amd64",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_containerimage",
            "read_context_entity",
            {"identifier": "image-key", "project": "my-project", "entity_id": "image-id"},
            {
                "identifier": "image-key",
                "entity_type": EntityTypes.CONTAINERIMAGE.value,
                "project": "my-project",
                "entity_id": "image-id",
            },
        ),
        (
            "get_containerimage_versions",
            "read_context_entity_versions",
            {"identifier": "api", "project": "my-project"},
            {"identifier": "api", "entity_type": EntityTypes.CONTAINERIMAGE.value, "project": "my-project"},
        ),
        (
            "list_containerimages",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "api",
                "kind": "container-image",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.CONTAINERIMAGE.value,
                "q": "query",
                "name": "api",
                "kind": "container-image",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "import_containerimage",
            "import_context_entity",
            {"file": "image.yaml", "key": "image-key", "reset_id": True, "context": "project"},
            None,
        ),
        ("load_containerimage", "load_context_entity", {"file": "image.yaml"}, None),
        (
            "delete_containerimage",
            "delete_context_entity",
            {
                "identifier": "api",
                "project": "my-project",
                "entity_id": "image-id",
                "delete_all_versions": True,
                "cascade": False,
            },
            {
                "identifier": "api",
                "entity_type": EntityTypes.CONTAINERIMAGE.value,
                "project": "my-project",
                "entity_id": "image-id",
                "delete_all_versions": True,
                "cascade": False,
            },
        ),
    ],
)
def test_containerimage_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict | None,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(containerimage_crud.crud_processor, processor_name, processor)

    result = getattr(containerimage_crud, function_name)(**kwargs)

    assert result == "result"
    if function_name == "import_containerimage":
        processor.assert_called_once_with(
            kwargs["file"],
            kwargs["key"],
            kwargs["reset_id"],
            kwargs["context"],
        )
    elif function_name == "load_containerimage":
        processor.assert_called_once_with(kwargs["file"])
    else:
        processor.assert_called_once_with(**expected_kwargs)


def test_update_containerimage_delegates_entity_fields(monkeypatch) -> None:
    entity = SimpleNamespace(
        project="my-project",
        ENTITY_TYPE=EntityTypes.CONTAINERIMAGE.value,
        id="image-id",
        to_dict=Mock(return_value={"spec": {"image": "api:latest"}}),
    )
    update_entity = Mock(return_value="containerimage")
    monkeypatch.setattr(containerimage_crud.crud_processor, "update_context_entity", update_entity)

    result = containerimage_crud.update_containerimage(entity)

    assert result == "containerimage"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.CONTAINERIMAGE.value,
        entity_id="image-id",
        entity_dict={"spec": {"image": "api:latest"}},
    )
