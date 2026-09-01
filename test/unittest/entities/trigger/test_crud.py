from unittest.mock import Mock

import pytest

import digitalhub.entities.trigger.crud as trigger_crud
from digitalhub.entities._commons.enums import EntityTypes


@pytest.mark.parametrize(
    ("executable_kwargs", "expected_executable", "template"),
    [
        (
            {"function": "store://function"},
            {"function": "store://function"},
            {"custom": "value"},
        ),
        (
            {"workflow": "store://workflow", "function": "store://ignored"},
            {"workflow": "store://workflow"},
            None,
        ),
    ],
)
def test_new_trigger_builds_executable_template(
    executable_kwargs: dict,
    expected_executable: dict,
    template: dict | None,
    monkeypatch,
) -> None:
    create_entity = Mock(return_value="trigger")
    monkeypatch.setattr(trigger_crud.crud_processor, "create_context_entity", create_entity)

    result = trigger_crud.new_trigger(
        project="my-project",
        name="on-demand",
        kind="lifecycle",
        task="store://task",
        uuid="trigger-id",
        description="A trigger",
        labels=["production"],
        embedded=True,
        template=template,
        **executable_kwargs,
    )

    assert result == "trigger"
    expected_template = {
        **({"custom": "value"} if template else {}),
        "task": "store://task",
        **expected_executable,
        "local_execution": False,
    }
    create_entity.assert_called_once_with(
        project="my-project",
        name="on-demand",
        kind="lifecycle",
        uuid="trigger-id",
        description="A trigger",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.TRIGGER.value,
        task="store://task",
        **expected_executable,
        template=expected_template,
    )


def test_new_trigger_requires_function_or_workflow(monkeypatch) -> None:
    create_entity = Mock()
    monkeypatch.setattr(trigger_crud.crud_processor, "create_context_entity", create_entity)

    with pytest.raises(ValueError, match="Workflow or function must be provided"):
        trigger_crud.new_trigger(
            project="my-project",
            name="trigger",
            kind="lifecycle",
            task="store://task",
        )

    create_entity.assert_not_called()


def test_new_trigger_rejects_non_dictionary_template() -> None:
    with pytest.raises(TypeError, match="Template must be a dictionary"):
        trigger_crud.new_trigger(
            project="my-project",
            name="trigger",
            kind="lifecycle",
            task="store://task",
            function="store://function",
            template="invalid",
        )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_trigger",
            "read_context_entity",
            {"identifier": "trigger-key", "project": "my-project", "entity_id": "trigger-id"},
            {
                "identifier": "trigger-key",
                "entity_type": EntityTypes.TRIGGER.value,
                "project": "my-project",
                "entity_id": "trigger-id",
            },
        ),
        (
            "list_triggers",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "on-demand",
                "kind": "lifecycle",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
                "task": "store://task",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.TRIGGER.value,
                "q": "query",
                "name": "on-demand",
                "kind": "lifecycle",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
                "task": "store://task",
            },
        ),
        (
            "delete_trigger",
            "delete_context_entity",
            {"identifier": "trigger-key", "project": "my-project", "entity_id": "trigger-id"},
            {
                "identifier": "trigger-key",
                "entity_type": EntityTypes.TRIGGER.value,
                "project": "my-project",
                "entity_id": "trigger-id",
            },
        ),
    ],
)
def test_trigger_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(trigger_crud.crud_processor, processor_name, processor)

    result = getattr(trigger_crud, function_name)(**kwargs)

    assert result == "result"
    processor.assert_called_once_with(**expected_kwargs)


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_args"),
    [
        (
            "import_trigger",
            "import_context_entity",
            {"file": "trigger.yaml", "key": "trigger-key", "reset_id": True, "context": "project"},
            ("trigger.yaml", "trigger-key", True, "project"),
        ),
        ("load_trigger", "load_context_entity", {"file": "trigger.yaml"}, ("trigger.yaml",)),
    ],
)
def test_trigger_import_and_load_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_args: tuple,
    monkeypatch,
) -> None:
    processor = Mock(return_value="trigger")
    monkeypatch.setattr(trigger_crud.crud_processor, processor_name, processor)

    result = getattr(trigger_crud, function_name)(**kwargs)

    assert result == "trigger"
    processor.assert_called_once_with(*expected_args)


def test_update_trigger_delegates_entity_fields(monkeypatch) -> None:
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = EntityTypes.TRIGGER.value
    entity.id = "trigger-id"
    entity.to_dict.return_value = {"metadata": {"name": "on-demand"}}
    update_entity = Mock(return_value="trigger")
    monkeypatch.setattr(trigger_crud.crud_processor, "update_context_entity", update_entity)

    result = trigger_crud.update_trigger(entity)

    assert result == "trigger"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.TRIGGER.value,
        entity_id="trigger-id",
        entity_dict={"metadata": {"name": "on-demand"}},
    )
