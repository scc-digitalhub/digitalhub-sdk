# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import replace
from unittest.mock import Mock

import pytest
from requests import Response

from digitalhub.stores.client.client import Client
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.utils.exceptions import ClientError


class TokenIdentity:
    """Auth provider whose token changes when the backend rejects it."""

    def __init__(self, proxy: str | None = "https://proxy.test") -> None:
        self.proxy = proxy
        self.token = "expired"
        self.rejected: list[BackendReq] = []

    def get_endpoint(self) -> str:
        return "https://core.test"

    def get_proxy(self) -> str | None:
        return self.proxy

    def authenticate(self, backend_request: BackendReq) -> BackendReq:
        return replace(backend_request, headers={**backend_request.headers, "Authorization": f"Bearer {self.token}"})

    def invalidate(self, rejected: BackendReq) -> bool:
        self.rejected.append(rejected)
        self.token = "refreshed"
        return True


def _response(status_code: int) -> Response:
    response = Response()
    response.status_code = status_code
    return response


def test_proxy_request_reaches_the_service_through_the_configured_proxy() -> None:
    transport = Mock()
    transport.execute.return_value = _response(500)
    client = Client(transport, TokenIdentity())

    response = client.proxy_request(
        "model.ns:8080",
        "POST",
        "/v2/models/model/infer",
        json={"inputs": []},
        headers={"Accept": "application/json"},
    )

    # Returned as is: an error of the service is not an error of Core.
    assert response is transport.execute.return_value
    sent = transport.execute.call_args.args[0]
    assert (sent.method, sent.api) == ("POST", "https://proxy.test/v2/models/model/infer")
    assert sent.headers == {
        "Accept": "application/json",
        "X-Proxy-Host": "model.ns:8080",
        "Authorization": "Bearer expired",
    }
    assert sent.to_transport_kwargs()["json"] == {"inputs": []}


def test_proxy_request_refreshes_the_credentials_once_when_rejected() -> None:
    identity = TokenIdentity()
    transport = Mock()
    transport.execute.side_effect = [_response(401), _response(401)]
    client = Client(transport, identity)

    response = client.proxy_request("model.ns:8080", "GET", "/health")

    assert response.status_code == 401
    assert len(identity.rejected) == 1
    assert transport.execute.call_count == 2
    assert transport.execute.call_args.args[0].headers["Authorization"] == "Bearer refreshed"


def test_proxy_request_without_a_proxy_raises() -> None:
    transport = Mock()
    client = Client(transport, TokenIdentity(proxy=None))

    with pytest.raises(ClientError, match="set DHCORE_PROXY"):
        client.proxy_request("model.ns:8080", "GET", "/health")

    transport.execute.assert_not_called()
