from unittest.mock import Mock

import pytest

import digitalhub.entities.run.crud as run_crud
from digitalhub.entities._commons.enums import EntityTypes


def test_new_run_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="run")
    monkeypatch.setattr(run_crud.crud_processor, "create_context_entity", create_entity)

    result = run_crud.new_run(
        project="my-project",
        kind="python+run",
        uuid="run-id",
        name="job-run",
        labels=["production"],
        task="store://task",
        action="execute",
    )

    assert result == "run"
    create_entity.assert_called_once_with(
        project="my-project",
        kind="python+run",
        uuid="run-id",
        name="job-run",
        labels=["production"],
        task="store://task",
        entity_type=EntityTypes.RUN.value,
        action="execute",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_run",
            "read_unversioned_entity",
            {"identifier": "run-id", "project": "my-project"},
            {
                "identifier": "run-id",
                "entity_type": EntityTypes.RUN.value,
                "project": "my-project",
            },
        ),
        (
            "list_runs",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "job-run",
                "kind": "python+run",
                "user": "user",
                "state": "RUNNING",
                "created": "created",
                "updated": "updated",
                "function": "store://function",
                "workflow": "store://workflow",
                "task": "store://task",
                "action": "execute",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.RUN.value,
                "q": "query",
                "name": "job-run",
                "kind": "python+run",
                "user": "user",
                "state": "RUNNING",
                "created": "created",
                "updated": "updated",
                "function": "store://function",
                "workflow": "store://workflow",
                "task": "store://task",
                "action": "execute",
            },
        ),
        (
            "delete_run",
            "delete_context_entity",
            {"identifier": "run-id", "project": "my-project", "entity_id": "run-id"},
            {
                "identifier": "run-id",
                "entity_type": EntityTypes.RUN.value,
                "project": "my-project",
                "entity_id": "run-id",
                "unversioned": True,
            },
        ),
    ],
)
def test_run_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(run_crud.crud_processor, processor_name, processor)

    result = getattr(run_crud, function_name)(**kwargs)

    assert result == "result"
    processor.assert_called_once_with(**expected_kwargs)


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_args"),
    [
        (
            "import_run",
            "import_context_entity",
            {"file": "run.yaml", "key": "run-key", "reset_id": True, "context": "project"},
            ("run.yaml", "run-key", True, "project"),
        ),
        ("load_run", "load_context_entity", {"file": "run.yaml"}, ("run.yaml",)),
    ],
)
def test_run_import_and_load_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_args: tuple,
    monkeypatch,
) -> None:
    processor = Mock(return_value="run")
    monkeypatch.setattr(run_crud.crud_processor, processor_name, processor)

    result = getattr(run_crud, function_name)(**kwargs)

    assert result == "run"
    processor.assert_called_once_with(*expected_args)


def test_update_run_delegates_entity_fields(monkeypatch) -> None:
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = EntityTypes.RUN.value
    entity.id = "run-id"
    entity.to_dict.return_value = {"status": {"state": "RUNNING"}}
    update_entity = Mock(return_value="run")
    monkeypatch.setattr(run_crud.crud_processor, "update_context_entity", update_entity)

    result = run_crud.update_run(entity)

    assert result == "run"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.RUN.value,
        entity_id="run-id",
        entity_dict={"status": {"state": "RUNNING"}},
    )
