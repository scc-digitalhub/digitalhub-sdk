from unittest.mock import Mock

import digitalhub.entities._processors.base.special_ops as special_ops_module
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor


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
