# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest
from requests import Response

from digitalhub.stores.client.client import Client
from digitalhub.stores.client.common.config import ClientConfig, get_client_config
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.common.utils import with_bearer_token
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.targets import BaseEntityTarget
from digitalhub.utils.exceptions import ClientError, UnauthorizedError

READ_PROJECT = ClientOp(
    category=ApiType.BASE,
    operation=BackendOp.READ,
    target=BaseEntityTarget("project", "demo"),
)


def _response(status_code: int, body: str) -> Response:
    response = Response()
    response.status_code = status_code
    response.url = "https://core.example/api/v1/projects/demo"
    response.headers = {}
    response._content = body.encode()
    return response


def _auth(token: str) -> Mock:
    auth = Mock(name=token)
    auth.get_endpoint.return_value = "https://core.example"
    auth.authenticate.side_effect = lambda request: with_bearer_token(request, token)
    auth.invalidate.return_value = True
    return auth


def _sent(transport: Mock) -> list:
    return [call.args[0] for call in transport.execute.call_args_list]


def test_clients_send_with_their_own_timeout_without_global_configuration() -> None:
    global_config = get_client_config()
    transport = Mock()
    transport.execute.side_effect = lambda request, **_: _response(200, '{"name": "demo"}')

    Client(transport, _auth("token"), ClientConfig(http_timeout=5)).execute(READ_PROJECT)
    Client(transport, _auth("token"), ClientConfig(http_timeout=7)).execute(READ_PROJECT)

    assert [request.timeout for request in _sent(transport)] == [5, 7]
    assert get_client_config() is global_config


def test_clients_with_different_credentials_share_one_transport() -> None:
    transport = Mock()
    transport.execute.side_effect = lambda request, **_: _response(200, '{"name": "demo"}')
    first = Client(transport, _auth("first"))
    second = Client(transport, _auth("second"))

    first.execute(READ_PROJECT)
    second.execute(READ_PROJECT)

    assert [request.headers["Authorization"] for request in _sent(transport)] == [
        "Bearer first",
        "Bearer second",
    ]


def test_unauthorized_response_invalidates_only_the_client_that_received_it() -> None:
    first_auth = _auth("first")
    second_auth = _auth("second")
    transport = Mock()
    transport.execute.side_effect = [
        _response(401, "Unauthorized"),
        _response(401, "Unauthorized"),
        _response(200, '{"name": "demo"}'),
    ]
    first = Client(transport, first_auth)
    second = Client(transport, second_auth)

    with pytest.raises(UnauthorizedError):
        first.execute(READ_PROJECT)
    second.execute(READ_PROJECT)

    first_auth.invalidate.assert_called_once()
    second_auth.invalidate.assert_not_called()
    assert transport.execute.call_count == 3


def test_credential_operations_need_the_user_identity() -> None:
    client = Client(Mock(), _auth("project"))

    with pytest.raises(ClientError, match="user identity"):
        client.get_credentials_and_config()
