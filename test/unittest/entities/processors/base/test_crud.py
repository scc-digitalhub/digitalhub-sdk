from unittest.mock import Mock

import pytest

import digitalhub.entities._processors.base.crud as base_crud_module
from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor


def test_delete_project_preserves_context_when_backend_delete_fails(monkeypatch) -> None:
    processor = BaseEntityCRUDProcessor()
    processor._delete_base_entity = Mock(side_effect=RuntimeError("delete failed"))
    delete_context = Mock()
    monkeypatch.setattr(base_crud_module, "delete_context", delete_context)
    monkeypatch.setattr(base_crud_module, "get_client", Mock(return_value=Mock()))

    with pytest.raises(RuntimeError, match="delete failed"):
        processor.delete_project_entity("project", "example")

    delete_context.assert_not_called()
