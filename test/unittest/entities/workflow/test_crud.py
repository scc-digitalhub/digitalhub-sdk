from unittest.mock import Mock

import pytest

import digitalhub.entities.workflow.crud as workflow_crud
from digitalhub.entities._commons.enums import EntityTypes


def test_new_workflow_delegates_to_context_processor(monkeypatch) -> None:
    create_entity = Mock(return_value="workflow")
    monkeypatch.setattr(workflow_crud.crud_processor, "create_context_entity", create_entity)

    result = workflow_crud.new_workflow(
        project="my-project",
        name="pipeline",
        kind="kfp",
        uuid="workflow-id",
        version="1",
        description="A workflow",
        labels=["production"],
        embedded=True,
        code_src="pipeline.py",
        handler="pipeline",
    )

    assert result == "workflow"
    create_entity.assert_called_once_with(
        project="my-project",
        name="pipeline",
        kind="kfp",
        uuid="workflow-id",
        version="1",
        description="A workflow",
        labels=["production"],
        embedded=True,
        entity_type=EntityTypes.WORKFLOW.value,
        code_src="pipeline.py",
        handler="pipeline",
    )


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_kwargs"),
    [
        (
            "get_workflow",
            "read_context_entity",
            {"identifier": "workflow-key", "project": "my-project", "entity_id": "workflow-id"},
            {
                "identifier": "workflow-key",
                "entity_type": EntityTypes.WORKFLOW.value,
                "project": "my-project",
                "entity_id": "workflow-id",
            },
        ),
        (
            "get_workflow_versions",
            "read_context_entity_versions",
            {"identifier": "pipeline", "project": "my-project"},
            {"identifier": "pipeline", "entity_type": EntityTypes.WORKFLOW.value, "project": "my-project"},
        ),
        (
            "list_workflows",
            "list_context_entities",
            {
                "project": "my-project",
                "q": "query",
                "name": "pipeline",
                "kind": "kfp",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
            {
                "project": "my-project",
                "entity_type": EntityTypes.WORKFLOW.value,
                "q": "query",
                "name": "pipeline",
                "kind": "kfp",
                "user": "user",
                "state": "READY",
                "created": "created",
                "updated": "updated",
                "versions": "all",
            },
        ),
        (
            "delete_workflow",
            "delete_context_entity",
            {
                "identifier": "pipeline",
                "project": "my-project",
                "entity_id": "workflow-id",
                "delete_all_versions": True,
                "cascade": False,
            },
            {
                "identifier": "pipeline",
                "entity_type": EntityTypes.WORKFLOW.value,
                "project": "my-project",
                "entity_id": "workflow-id",
                "delete_all_versions": True,
                "cascade": False,
            },
        ),
    ],
)
def test_workflow_operations_delegate_to_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_kwargs: dict,
    monkeypatch,
) -> None:
    processor = Mock(return_value="result")
    monkeypatch.setattr(workflow_crud.crud_processor, processor_name, processor)

    result = getattr(workflow_crud, function_name)(**kwargs)

    assert result == "result"
    processor.assert_called_once_with(**expected_kwargs)


@pytest.mark.parametrize(
    ("function_name", "processor_name", "kwargs", "expected_args"),
    [
        (
            "import_workflow",
            "import_executable_entity",
            {"file": "workflow.yaml", "key": "workflow-key", "reset_id": True, "context": "project"},
            ("workflow.yaml", "workflow-key", True, "project"),
        ),
        ("load_workflow", "load_executable_entity", {"file": "workflow.yaml"}, ("workflow.yaml",)),
    ],
)
def test_workflow_import_and_load_delegate_to_executable_processor(
    function_name: str,
    processor_name: str,
    kwargs: dict,
    expected_args: tuple,
    monkeypatch,
) -> None:
    processor = Mock(return_value="workflow")
    monkeypatch.setattr(workflow_crud.executable_processor, processor_name, processor)

    result = getattr(workflow_crud, function_name)(**kwargs)

    assert result == "workflow"
    processor.assert_called_once_with(*expected_args)


def test_update_workflow_delegates_entity_fields(monkeypatch) -> None:
    entity = Mock()
    entity.project = "my-project"
    entity.ENTITY_TYPE = EntityTypes.WORKFLOW.value
    entity.id = "workflow-id"
    entity.to_dict.return_value = {"metadata": {"name": "pipeline"}}
    update_entity = Mock(return_value="workflow")
    monkeypatch.setattr(workflow_crud.crud_processor, "update_context_entity", update_entity)

    result = workflow_crud.update_workflow(entity)

    assert result == "workflow"
    update_entity.assert_called_once_with(
        project="my-project",
        entity_type=EntityTypes.WORKFLOW.value,
        entity_id="workflow-id",
        entity_dict={"metadata": {"name": "pipeline"}},
    )
