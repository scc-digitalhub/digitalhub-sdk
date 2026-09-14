from unittest.mock import Mock

from digitalhub.stores.client.base.client import Client
from digitalhub.stores.client.common.config import get_client_config


def test_validate_credentials_uses_the_http_handler_auth_check() -> None:
    http_handler = Mock()
    client = Client(
        configurator=Mock(),
        api_builder=Mock(),
        params_builder=Mock(),
        http_handler=http_handler,
    )

    client.validate_credentials()

    http_handler.execute_request.assert_called_once_with(
        "GET",
        get_client_config().api_auth_check,
    )


def test_get_k8s_resource_profiles_uses_the_http_handler() -> None:
    http_handler = Mock()
    http_handler.execute_request.return_value = {
        get_client_config().k8s_resource_profiles: ["gpu", "cpu"],
    }
    client = Client(
        configurator=Mock(),
        api_builder=Mock(),
        params_builder=Mock(),
        http_handler=http_handler,
    )

    result = client.get_k8s_resource_profiles()

    assert result == ["gpu", "cpu"]
    http_handler.execute_request.assert_called_once_with(
        "GET",
        get_client_config().well_known_conf,
    )
