from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.entities._commons.enums import EntityTypes, OpType
from digitalhub.entities.project._base.crud_manager import EntityCRUD


def _manager(operations: dict[OpType, Mock]) -> EntityCRUD:
    manager = EntityCRUD("my-project", EntityTypes.FUNCTION)
    manager._ops = operations
    return manager


def test_new_injects_project_into_operation() -> None:
    operation = Mock(return_value="function")
    manager = _manager({OpType.NEW: operation})

    result = manager.new(name="handler")

    assert result == "function"
    operation.assert_called_once_with(name="handler", project="my-project")


def test_operation_does_not_override_explicit_project() -> None:
    operation = Mock(return_value="function")
    manager = _manager({OpType.GET: operation})

    result = manager.get("function-key", project="other-project")

    assert result == "function"
    operation.assert_called_once_with("function-key", project="other-project")


@pytest.mark.parametrize(
    ("method_name", "operation_type", "args", "kwargs"),
    [
        ("log", OpType.LOG_GENERIC, (), {"kind": "custom-function"}),
        ("register", OpType.REGISTER_GENERIC, (), {"kind": "custom-function"}),
        ("get_versions", OpType.GET_VERSIONS, ("handler",), {}),
        ("load", OpType.LOAD, ("function.yaml",), {}),
        ("delete", OpType.DELETE, ("function-key",), {"cascade": False}),
    ],
)
def test_operations_dispatch_and_inject_project(
    method_name: str,
    operation_type: OpType,
    args: tuple,
    kwargs: dict,
) -> None:
    operation = Mock(return_value="result")
    manager = _manager({operation_type: operation})

    result = getattr(manager, method_name)(*args, **kwargs)

    assert result == "result"
    operation.assert_called_once_with(*args, project="my-project", **kwargs)


def test_import_entity_forces_manager_project_as_context() -> None:
    operation = Mock(return_value="function")
    manager = _manager({OpType.IMPORT: operation})

    result = manager.import_entity(file="function.yaml", context="other-project")

    assert result == "function"
    operation.assert_called_once_with(file="function.yaml", context="my-project")


def test_list_passes_project_as_first_argument() -> None:
    operation = Mock(return_value=["function"])
    manager = _manager({OpType.LIST: operation})

    result = manager.list(state="READY")

    assert result == ["function"]
    operation.assert_called_once_with("my-project", state="READY")


def test_update_rejects_entity_from_another_project() -> None:
    operation = Mock()
    manager = _manager({OpType.UPDATE: operation})
    entity = SimpleNamespace(project="other-project")

    with pytest.raises(ValueError, match="Entity to update is not in project my-project"):
        manager.update(entity)

    operation.assert_not_called()


def test_update_passes_entity_to_operation() -> None:
    operation = Mock(return_value="updated")
    manager = _manager({OpType.UPDATE: operation})
    entity = SimpleNamespace(project="my-project")

    result = manager.update(entity)

    assert result == "updated"
    operation.assert_called_once_with(entity)


def test_unsupported_operation_has_entity_context() -> None:
    manager = _manager({})

    with pytest.raises(AttributeError, match="Operation 'new' not available for function"):
        manager.new(name="handler")
