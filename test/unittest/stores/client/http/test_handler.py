from unittest.mock import Mock

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException
from requests.exceptions import Timeout as RequestsTimeout

import digitalhub.stores.client.http.handler as handler_module
import digitalhub.stores.client.http.transport as transport_module
from digitalhub.stores.client.http.handler import HttpRequestHandler
from digitalhub.utils.exceptions import BackendError, UnauthorizedError


def test_request_refreshes_credentials_only_once(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"
    configurator.get_auth_parameters.side_effect = lambda kwargs: kwargs
    configurator.evaluate_refresh.return_value = True

    request = Mock(return_value=object())
    monkeypatch.setattr(handler_module, "request", request)

    handler = HttpRequestHandler(configurator)
    handler._response_processor = Mock()
    handler._response_processor.process.side_effect = [UnauthorizedError(), UnauthorizedError()]

    with pytest.raises(UnauthorizedError):
        handler.execute_request("GET", "/resource")

    assert request.call_count == 2
    configurator.evaluate_refresh.assert_called_once_with()


def test_request_returns_replay_result_after_refresh(monkeypatch) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"
    configurator.get_auth_parameters.side_effect = (
        lambda kwargs: {**kwargs, "headers": {"Authorization": "Bearer refreshed"}}
    )
    configurator.evaluate_refresh.return_value = True

    request = Mock(return_value=object())
    monkeypatch.setattr(handler_module, "request", request)

    handler = HttpRequestHandler(configurator)
    handler._response_processor = Mock()
    handler._response_processor.process.side_effect = [UnauthorizedError(), {"result": "ok"}]

    result = handler.execute_request("GET", "/resource")

    assert result == {"result": "ok"}
    assert request.call_count == 2
    assert request.call_args.kwargs["headers"] == {"Authorization": "Bearer refreshed"}


@pytest.mark.parametrize(
    ("transport_error", "expected_error", "message"),
    [
        (RequestsTimeout(), TimeoutError, "Request to DHCore backend timed out."),
        (RequestsConnectionError(), ConnectionError, "Unable to connect to DHCore backend."),
        (RequestException("broken transport"), BackendError, "Some error occurred. broken transport"),
    ],
)
def test_request_normalizes_transport_errors(monkeypatch, transport_error, expected_error, message) -> None:
    configurator = Mock()
    configurator.get_endpoint.return_value = "https://example.test"
    configurator.get_auth_parameters.side_effect = lambda kwargs: kwargs
    monkeypatch.setattr(transport_module, "requests_request", Mock(side_effect=transport_error))

    handler = HttpRequestHandler(configurator)

    with pytest.raises(expected_error, match=message) as exc_info:
        handler.execute_request("GET", "/resource")

    assert exc_info.value.__cause__ is transport_error
