from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities.secret.crud as secret_crud
from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.utils.exceptions import EntityNotExistsError


def test_new_secret_creates_entity_and_sets_secret_value(monkeypatch) -> None:
    entity = Mock()
    create_entity = Mock(return_value=entity)
    monkeypatch.setattr(secret_crud.crud_processor, "create_context_entity", create_entity)

    result = secret_crud.new_secret(
        project="my-project",
        name="api-key",
        uuid="secret-id",
        description="An API key",
        labels=["production"],
        embedded=True,
        secret_value="secret-value",
        provider="vault",
    )

    assert result is entity
    create_entity.assert_called_once_with(
        project="my-project",
        name="api-key",
        kind=EntityKinds.SECRET_SECRET.value,
        uuid="secret-id",
        description="An API key",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.SECRET.value,
        provider="vault",
    )
    entity.set_secret_value.assert_called_once_with(value="secret-value")


def test_new_secret_requires_secret_value(monkeypatch) -> None:
    create_entity = Mock()
    monkeypatch.setattr(secret_crud.crud_processor, "create_context_entity", create_entity)

    with pytest.raises(ValueError, match="secret_value must be provided"):
        secret_crud.new_secret(project="my-project", name="api-key")

    create_entity.assert_not_called()


def test_get_secret_by_key_delegates_to_processor(monkeypatch) -> None:
    entity = object()
    read_entity = Mock(return_value=entity)
    monkeypatch.setattr(secret_crud, "is_valid_key", Mock(return_value=True))
    monkeypatch.setattr(secret_crud.crud_processor, "read_context_entity", read_entity)

    result = secret_crud.get_secret(
        identifier="store://secret-key",
        project="my-project",
        entity_id="secret-id",
    )

    assert result is entity
    read_entity.assert_called_once_with(
        identifier="store://secret-key",
        entity_type=EntityTypes.SECRET.value,
        project="my-project",
        entity_id="secret-id",
    )


def test_get_secret_by_name_searches_list(monkeypatch) -> None:
    matching = SimpleNamespace(name="api-key")
    monkeypatch.setattr(secret_crud, "is_valid_key", Mock(return_value=False))
    list_secrets = Mock(return_value=[SimpleNamespace(name="other"), matching])
    monkeypatch.setattr(secret_crud, "list_secrets", list_secrets)

    result = secret_crud.get_secret(identifier="api-key", project="my-project")

    assert result is matching
    list_secrets.assert_called_once_with(project="my-project")


def test_get_secret_by_name_requires_project(monkeypatch) -> None:
    monkeypatch.setattr(secret_crud, "is_valid_key", Mock(return_value=False))

    with pytest.raises(ValueError, match="Project must be provided"):
        secret_crud.get_secret(identifier="api-key")


def test_get_secret_by_name_raises_when_missing(monkeypatch) -> None:
    monkeypatch.setattr(secret_crud, "is_valid_key", Mock(return_value=False))
    monkeypatch.setattr(secret_crud, "list_secrets", Mock(return_value=[]))

    with pytest.raises(EntityNotExistsError, match="Secret api-key not found"):
        secret_crud.get_secret(identifier="api-key", project="my-project")


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "list_secrets",
            "list_context_entities",
            {"project": "my-project"},
            {"project": "my-project", "entity_type": EntityTypes.SECRET.value},
        ),
        (
            "import_secret",
            "import_context_entity",
            {"file": "secret.yaml", "key": "secret-key", "reset_id": True, "context": "project"},
            None,
        ),
        ("load_secret", "load_context_entity", {"file": "secret.yaml"}, None),
        (
            "delete_secret",
            "delete_context_entity",
            {
                "identifier": "api-key",
                "project": "my-project",
                "entity_id": "secret-id",
                "delete_all_versions": True,
            },
            {
                "identifier": "api-key",
                "entity_type": EntityTypes.SECRET.value,
                "project": "my-project",
                "entity_id": "secret-id",
                "delete_all_versions": True,
            },
        ),
    ],
)
def test_secret_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict | None,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(secret_crud.crud_processor, processor_name, processor)

    result = getattr(secret_crud, function_name)(**kwargs)

    assert result == "result"
    if function_name == "import_secret":
        processor.assert_called_once_with(
            kwargs["file"],
            kwargs["key"],
            kwargs["reset_id"],
            kwargs["context"],
        )
    elif function_name == "load_secret":
        processor.assert_called_once_with(kwargs["file"])
    else:
        processor.assert_called_once_with(**expected_kwargs)


def test_update_secret_delegates_entity_fields(monkeypatch) -> None:
    entity = SimpleNamespace(
        project="my-project",
        ENTITY_TYPE=EntityTypes.SECRET.value,
        id="secret-id",
        to_dict=Mock(return_value={"metadata": {"name": "api-key"}}),
    )
    update_entity = Mock(return_value="secret")
    monkeypatch.setattr(secret_crud.crud_processor, "update_context_entity", update_entity)

    result = secret_crud.update_secret(entity)

    assert result == "secret"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.SECRET.value,
        entity_id="secret-id",
        entity_dict={"metadata": {"name": "api-key"}},
    )
