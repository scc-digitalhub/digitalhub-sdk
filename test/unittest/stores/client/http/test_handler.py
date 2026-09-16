# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest
from requests import PreparedRequest, Response
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException
from requests.exceptions import Timeout as RequestsTimeout

import digitalhub.stores.client.http.transport as transport_module
from digitalhub.stores.client.common.enums import OpsType
from digitalhub.stores.client.common.utils import (
    next_page,
    with_basic_auth,
    with_bearer_token,
    with_data,
    with_json_content_type,
    with_pagination,
)
from digitalhub.stores.client.http.handler import HttpRequestHandler
from digitalhub.stores.client.http.request import BackendReq
from digitalhub.stores.client.http.transport import HttpTransport
from digitalhub.utils.exceptions import BackendError, ForbiddenError, UnauthorizedError


def test_backend_request_is_immutable_and_preserves_http_details() -> None:
    backend_request = BackendReq(
        method="GET",
        api="/resource",
        operation=OpsType.ENTITY_READ,
        params={"name": "demo"},
        headers={"Authorization": "Bearer token"},
        data="payload",
    )

    assert backend_request.method == "GET"
    assert backend_request.api == "/resource"
    assert backend_request.operation == OpsType.ENTITY_READ.value
    assert backend_request.params == {"name": "demo"}
    assert backend_request.headers == {"Authorization": "Bearer token"}
    assert backend_request.data == "payload"

    with pytest.raises(FrozenInstanceError):
        backend_request.method = "POST"

    with pytest.raises(TypeError):
        backend_request.params["name"] = "other"


def test_backend_request_uses_configured_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "digitalhub.stores.client.http.request.get_client_config",
        lambda: Mock(http_timeout=17),
    )

    backend_request = BackendReq(method="GET", api="/resource")

    assert backend_request.timeout == 17
    assert backend_request.to_transport_kwargs()["timeout"] == 17


def test_with_data_replaces_payload_without_mutating_request() -> None:
    backend_request = BackendReq(
        method="POST",
        api="/resource",
        params={"name": "demo"},
        headers={"X-Test": "value"},
        data="old-payload",
        options={"verify": False},
    )

    transformed_request = with_data(backend_request, "new-payload")

    assert transformed_request is not backend_request
    assert backend_request.data == "old-payload"
    assert transformed_request.data == "new-payload"
    assert transformed_request.params == backend_request.params
    assert transformed_request.headers == backend_request.headers
    assert transformed_request.options == backend_request.options


def test_request_transformations_are_copy_on_write(monkeypatch) -> None:
    monkeypatch.setattr(
        "digitalhub.stores.client.common.utils.get_client_config",
        lambda: Mock(default_page_start=0, default_page_size=10, default_sort="updated,DESC"),
    )
    backend_request = BackendReq(
        method="GET",
        api="/resource",
        params={"filter": "active"},
        headers={"X-Trace": "trace"},
        options={"verify": False},
    )

    transformed_request = with_pagination(
        with_json_content_type(
            with_bearer_token(
                with_basic_auth(backend_request, "user", "password"),
                "token",
            )
        )
    )

    assert backend_request.params == {"filter": "active"}
    assert backend_request.headers == {"X-Trace": "trace"}
    assert backend_request.options == {"verify": False}
    assert transformed_request.params == {
        "filter": "active",
        "page": 0,
        "size": 10,
        "sort": "updated,DESC",
    }
    assert transformed_request.headers == {
        "X-Trace": "trace",
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }
    assert transformed_request.to_transport_kwargs()["auth"] == ("user", "password")


def test_next_page_returns_request_with_incremented_page() -> None:
    backend_request = BackendReq(method="GET", api="/resource", params={"page": 2})

    next_request = next_page(backend_request)

    assert backend_request.params["page"] == 2
    assert next_request.params["page"] == 3


def test_handler_executes_structured_backend_request(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"
    configurator.authenticate.side_effect = lambda backend_request: backend_request

    transport = Mock()
    transport.execute.return_value = object()

    handler = HttpRequestHandler(configurator, transport)
    handler._response_processor = Mock()
    handler._response_processor.process.return_value = {"result": "ok"}

    result = handler.execute_request(
        BackendReq(
            method="POST",
            api="/resource",
            operation="entity.create",
            params={"name": "demo"},
            headers={"X-Test": "value"},
            data="payload",
            options={"json": {"trace": True}},
        )
    )

    assert result == {"result": "ok"}
    executed_request = transport.execute.call_args.args[0]
    assert executed_request == BackendReq(
        method="POST",
        api="https://example.test/resource",
        operation="entity.create",
        params={"name": "demo"},
        headers={"X-Test": "value"},
        data="payload",
        options={"json": {"trace": True}},
    )


def test_handler_preserves_absolute_url(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://core.example"
    configurator.authenticate.side_effect = AssertionError("authentication should be skipped")

    transport = Mock()
    transport.execute.return_value = object()

    handler = HttpRequestHandler(configurator, transport)
    handler._response_processor = Mock()
    handler._response_processor.process.return_value = {"result": "ok"}

    result = handler.execute_request(
        BackendReq(
            method="GET",
            api="https://issuer.example/token",
            operation=OpsType.AUTH_REFRESH,
            authenticate=False,
        ),
    )

    assert result == {"result": "ok"}
    assert transport.execute.call_args.args[0].api == "https://issuer.example/token"


def test_request_refreshes_credentials_only_once(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"
    configurator.authenticate.side_effect = lambda backend_request: backend_request
    configurator.evaluate_refresh.return_value = True

    transport = Mock()
    transport.execute.side_effect = [object(), object()]

    handler = HttpRequestHandler(configurator, transport)
    handler._response_processor = Mock()
    handler._response_processor.process.side_effect = [UnauthorizedError(), UnauthorizedError()]

    with pytest.raises(UnauthorizedError):
        handler.execute_request(BackendReq(method="GET", api="/resource"))

    assert transport.execute.call_count == 2
    configurator.evaluate_refresh.assert_called_once_with()


def test_request_returns_replay_result_after_refresh(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"

    def authenticate(backend_request: BackendReq) -> BackendReq:
        return BackendReq(
            method=backend_request.method,
            api=backend_request.api,
            operation=backend_request.operation,
            headers={"Authorization": "Bearer refreshed"},
            params=backend_request.params,
            data=backend_request.data,
            authenticate=backend_request.authenticate,
            options=backend_request.options,
        )

    configurator.authenticate.side_effect = authenticate
    configurator.evaluate_refresh.return_value = True

    transport = Mock()
    transport.execute.side_effect = [object(), object()]

    handler = HttpRequestHandler(configurator, transport)
    handler._response_processor = Mock()
    handler._response_processor.process.side_effect = [UnauthorizedError(), {"result": "ok"}]

    result = handler.execute_request(BackendReq(method="GET", api="/resource"))

    assert result == {"result": "ok"}
    assert transport.execute.call_count == 2
    assert transport.execute.call_args.args[0].headers == {"Authorization": "Bearer refreshed"}


def test_request_does_not_refresh_credentials_on_forbidden(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"
    configurator.authenticate.side_effect = lambda backend_request: backend_request

    transport = Mock()
    transport.execute.return_value = object()

    handler = HttpRequestHandler(configurator, transport)
    handler._response_processor = Mock()
    handler._response_processor.process.side_effect = ForbiddenError()

    with pytest.raises(ForbiddenError):
        handler.execute_request(BackendReq(method="GET", api="/resource"))

    configurator.evaluate_refresh.assert_not_called()
    assert transport.execute.call_count == 1


def test_request_logs_operation_attempt_and_full_request_details(monkeypatch, caplog) -> None:
    full_url = "https://example.test/api/v1/-/demo/functions/abc-123"
    request_data = "payload"
    response = Response()
    response.status_code = 200
    response.url = full_url
    response.headers = {}
    response._content = b'{"result": "ok"}'
    prepared_request = PreparedRequest()
    prepared_request.prepare(
        method="GET",
        url=full_url,
        headers={"Authorization": "Bearer token"},
        data=request_data,
    )
    response.request = prepared_request

    monkeypatch.setattr(transport_module, "requests_request", Mock(return_value=response))
    monkeypatch.setattr(transport_module.logger, "propagate", True)
    monkeypatch.setattr(logging.getLogger("dhcore"), "propagate", True)
    transport = HttpTransport()

    with caplog.at_level(logging.DEBUG, logger=transport_module.logger.name):
        result = transport.execute(
            BackendReq(
                method="GET",
                api=full_url,
                operation=OpsType.ENTITY_READ,
                data=request_data,
            ),
        )

    assert result is response
    assert "Operation: entity.read" in caplog.text
    assert "Attempt: 1" in caplog.text
    assert "Duration:" not in caplog.text
    assert full_url in caplog.text
    assert "Bearer token" in caplog.text
    assert request_data in caplog.text
    assert '{"result": "ok"}' in caplog.text


@pytest.mark.parametrize(
    ("transport_error", "expected_error", "message"),
    [
        (RequestsTimeout(), TimeoutError, "Request to DHCore backend timed out."),
        (RequestsConnectionError(), ConnectionError, "Unable to connect to DHCore backend."),
        (RequestException("broken transport"), BackendError, "Some error occurred. broken transport"),
    ],
)
def test_request_normalizes_transport_errors(monkeypatch, transport_error, expected_error, message) -> None:
    monkeypatch.setattr(transport_module, "requests_request", Mock(side_effect=transport_error))

    transport = HttpTransport()

    with pytest.raises(expected_error, match=message) as exc_info:
        transport.execute(BackendReq(method="GET", api="https://example.test/resource"))

    assert exc_info.value.__cause__ is transport_error


def test_transport_passes_backend_request_timeout(monkeypatch) -> None:
    response = Response()
    response.status_code = 200
    response.url = "https://example.test/resource"
    response.headers = {}
    response._content = b"{}"
    prepared_request = PreparedRequest()
    prepared_request.prepare(method="GET", url=response.url)
    response.request = prepared_request
    requests_request = Mock(return_value=response)
    monkeypatch.setattr(transport_module, "requests_request", requests_request)

    HttpTransport().execute(
        BackendReq(method="GET", api=response.url, timeout=7),
    )

    assert requests_request.call_args.kwargs["timeout"] == 7
