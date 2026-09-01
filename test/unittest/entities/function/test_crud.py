from unittest.mock import Mock

import pytest

import digitalhub.entities.function.crud as function_crud
from digitalhub.entities._commons.enums import EntityTypes


def test_new_function_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="function")
    monkeypatch.setattr(function_crud.crud_processor, "create_context_entity", create_entity)

    result = function_crud.new_function(
        project="my-project",
        name="handler",
        kind="python",
        uuid="function-id",
        version="1",
        description="A function",
        labels=["production"],
        embedded=True,
        code_src="function.py",
        handler="handler",
    )

    assert result == "function"
    create_entity.assert_called_once_with(
        project="my-project",
        name="handler",
        kind="python",
        uuid="function-id",
        version="1",
        description="A function",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.FUNCTION.value,
        code_src="function.py",
        handler="handler",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_function",
            "read_context_entity",
            {"identifier": "function-key", "project": "my-project", "entity_id": "function-id"},
            {
                "identifier": "function-key",
                "entity_type": EntityTypes.FUNCTION.value,
                "project": "my-project",
                "entity_id": "function-id",
            },
        ),
        (
            "get_function_versions",
            "read_context_entity_versions",
            {"identifier": "handler", "project": "my-project"},
            {"identifier": "handler", "entity_type": EntityTypes.FUNCTION.value, "project": "my-project"},
        ),
        (
            "list_functions",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "handler",
                "kind": "python",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.FUNCTION.value,
                "q": "query",
                "name": "handler",
                "kind": "python",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "delete_function",
            "delete_context_entity",
            {
                "identifier": "handler",
                "project": "my-project",
                "entity_id": "function-id",
                "delete_all_versions": True,
                "cascade": False,
            },
            {
                "identifier": "handler",
                "entity_type": EntityTypes.FUNCTION.value,
                "project": "my-project",
                "entity_id": "function-id",
                "delete_all_versions": True,
                "cascade": False,
            },
        ),
    ],
)
def test_function_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(function_crud.crud_processor, processor_name, processor)

    result = getattr(function_crud, function_name)(**kwargs)

    assert result == "result"
    processor.assert_called_once_with(**expected_kwargs)


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_args"),
    [
        (
            "import_function",
            "import_executable_entity",
            {"file": "function.yaml", "key": "function-key", "reset_id": True, "context": "project"},
            ("function.yaml", "function-key", True, "project"),
        ),
        ("load_function", "load_executable_entity", {"file": "function.yaml"}, ("function.yaml",)),
    ],
)
def test_function_import_and_load_delegate_to_executable_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_args: tuple,
    monkeypatch,
) -> None:
    processor = Mock(return_value="function")
    monkeypatch.setattr(function_crud.executable_processor, processor_name, processor)

    result = getattr(function_crud, function_name)(**kwargs)

    assert result == "function"
    processor.assert_called_once_with(*expected_args)


def test_update_function_delegates_entity_fields(monkeypatch) -> None:
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = EntityTypes.FUNCTION.value
    entity.id = "function-id"
    entity.to_dict.return_value = {"metadata": {"name": "handler"}}
    update_entity = Mock(return_value="function")
    monkeypatch.setattr(function_crud.crud_processor, "update_context_entity", update_entity)

    result = function_crud.update_function(entity)

    assert result == "function"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.FUNCTION.value,
        entity_id="function-id",
        entity_dict={"metadata": {"name": "handler"}},
    )
