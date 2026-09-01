from unittest.mock import Mock

import pytest

import digitalhub.entities._processors.base.special_ops as special_ops_module
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor


def test_build_project_key_uses_store_scheme() -> None:
    assert BaseEntitySpecialOpsProcessor().build_project_key("project-id") == "store://project-id"


def test_unshare_finds_user_after_first_acl_entry(monkeypatch) -> None:
    client = Mock()
    api = object()
    client.build_api.return_value = api
    client.read_object.return_value = [
        {"id": "alice-id", "user": "alice"},
        {"id": "bob-id", "user": "bob"},
    ]
    client.build_parameters.side_effect = lambda *args, **kwargs: kwargs
    monkeypatch.setattr(special_ops_module, "get_client", Mock(return_value=client))

    BaseEntitySpecialOpsProcessor().share_project_entity(
        entity_type="project",
        entity_name="example",
        user="bob",
        unshare=True,
    )

    client.delete_object.assert_called_once_with(
        api,
        unshare=True,
        user="bob",
        id="bob-id",
    )


def test_share_creates_access_with_built_parameters(monkeypatch) -> None:
    client = Mock()
    api = object()
    client.build_api.return_value = api
    client.build_parameters.side_effect = lambda *args, **kwargs: kwargs
    monkeypatch.setattr(special_ops_module, "get_client", Mock(return_value=client))

    result = BaseEntitySpecialOpsProcessor().share_project_entity(
        entity_type="project",
        entity_name="example",
        user="alice",
        role="reader",
    )

    assert result is None
    client.create_object.assert_called_once_with(
        api,
        obj={},
        unshare=False,
        user="alice",
        role="reader",
    )


def test_unshare_raises_when_user_has_no_access(monkeypatch) -> None:
    client = Mock()
    client.build_api.return_value = object()
    client.read_object.return_value = [{"id": "alice-id", "user": "alice"}]
    monkeypatch.setattr(special_ops_module, "get_client", Mock(return_value=client))

    with pytest.raises(ValueError, match="User 'bob' does not have access to project"):
        BaseEntitySpecialOpsProcessor().share_project_entity(
            entity_type="project",
            entity_name="example",
            user="bob",
            unshare=True,
        )
