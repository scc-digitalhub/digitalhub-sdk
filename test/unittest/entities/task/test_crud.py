from unittest.mock import Mock

import pytest

import digitalhub.entities.task.crud as task_crud
from digitalhub.entities._commons.enums import EntityTypes


def test_new_task_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="task")
    monkeypatch.setattr(task_crud.crud_processor, "create_context_entity", create_entity)

    result = task_crud.new_task(
        project="my-project",
        kind="python+job",
        uuid="task-id",
        name="job",
        labels=["production"],
        function="store://function",
        workflow="store://workflow",
        command="run",
    )

    assert result == "task"
    create_entity.assert_called_once_with(
        project="my-project",
        kind="python+job",
        uuid="task-id",
        name="job",
        labels=["production"],
        entity_type=EntityTypes.TASK.value,
        function="store://function",
        workflow="store://workflow",
        command="run",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_task",
            "read_unversioned_entity",
            {"identifier": "task-id", "project": "my-project"},
            {
                "identifier": "task-id",
                "entity_type": EntityTypes.TASK.value,
                "project": "my-project",
            },
        ),
        (
            "list_tasks",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "job",
                "kind": "python+job",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "function": "store://function",
                "workflow": "store://workflow",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.TASK.value,
                "q": "query",
                "name": "job",
                "kind": "python+job",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "function": "store://function",
                "workflow": "store://workflow",
            },
        ),
        (
            "delete_task",
            "delete_context_entity",
            {
                "identifier": "task-id",
                "project": "my-project",
                "entity_id": "task-id",
                "cascade": False,
            },
            {
                "identifier": "task-id",
                "entity_type": EntityTypes.TASK.value,
                "project": "my-project",
                "entity_id": "task-id",
                "cascade": False,
                "unversioned": True,
            },
        ),
    ],
)
def test_task_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(task_crud.crud_processor, processor_name, processor)

    result = getattr(task_crud, function_name)(**kwargs)

    assert result == "result"
    processor.assert_called_once_with(**expected_kwargs)


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_args"),
    [
        (
            "import_task",
            "import_context_entity",
            {"file": "task.yaml", "key": "task-key", "reset_id": True, "context": "project"},
            ("task.yaml", "task-key", True, "project"),
        ),
        ("load_task", "load_context_entity", {"file": "task.yaml"}, ("task.yaml",)),
    ],
)
def test_task_import_and_load_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_args: tuple,
    monkeypatch,
) -> None:
    processor = Mock(return_value="task")
    monkeypatch.setattr(task_crud.crud_processor, processor_name, processor)

    result = getattr(task_crud, function_name)(**kwargs)

    assert result == "task"
    processor.assert_called_once_with(*expected_args)


def test_update_task_delegates_entity_fields(monkeypatch) -> None:
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = EntityTypes.TASK.value
    entity.id = "task-id"
    entity.to_dict.return_value = {"metadata": {"name": "job"}}
    update_entity = Mock(return_value="task")
    monkeypatch.setattr(task_crud.crud_processor, "update_context_entity", update_entity)

    result = task_crud.update_task(entity)

    assert result == "task"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.TASK.value,
        entity_id="task-id",
        entity_dict={"metadata": {"name": "job"}},
    )
