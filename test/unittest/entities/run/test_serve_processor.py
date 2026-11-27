# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities.run._base.polling as polling_module
import digitalhub.entities.run._base.serve_processor as serve_module
from digitalhub.entities._commons.enums import State
from digitalhub.entities.run._base.serve_processor import RunServeProcessor
from digitalhub.utils.exceptions import EntityError


def _serve_run(service: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id="run-id",
        project="project",
        kind="function+serve:run",
        spec=SimpleNamespace(task="function+serve://project/function:function-id"),
        status=SimpleNamespace(state=State.RUNNING.value, service=service),
        _direct_service=None,
    )


def _clock(monkeypatch, *values: float) -> Mock:
    sleep = Mock()
    clock_values = iter(values)
    monkeypatch.setattr(
        polling_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )
    return sleep


def test_wait_returns_when_the_service_is_published(monkeypatch) -> None:
    # Core publishes the service while the run stays RUNNING: waiting for a
    # terminal state would never end.
    processor = RunServeProcessor(Mock())
    run = _serve_run()
    services = iter([None, {"url": "model.ns:8080"}])
    processor.crud_processor.refresh_context_entity = Mock(
        side_effect=lambda run: setattr(run.status, "service", next(services))
    )
    sleep = _clock(monkeypatch, 0.0, 0.0, 1.0)

    assert processor.wait(run, log_info=False, poll_interval=1) is run

    assert processor.crud_processor.refresh_context_entity.call_count == 2
    sleep.assert_called_once_with(1)


def test_wait_returns_when_the_deployment_fails(monkeypatch) -> None:
    processor = RunServeProcessor(Mock())
    run = _serve_run()
    processor.crud_processor.refresh_context_entity = Mock(
        side_effect=lambda run: setattr(run.status, "state", State.ERROR.value)
    )
    _clock(monkeypatch, 0.0, 0.0)

    assert processor.wait(run, log_info=False) is run


def test_wait_honours_the_timeout(monkeypatch) -> None:
    # The runtimes waited 300 s whatever the timeout, then returned as if the
    # service were up.
    processor = RunServeProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock()
    _clock(monkeypatch, 0.0, 0.0, 1.0, 2.0)

    with pytest.raises(TimeoutError, match="Run run-id did not deploy its service within 2s"):
        processor.wait(_serve_run(), log_info=False, timeout=2, poll_interval=1)


def test_a_run_of_a_runtime_not_installed_is_not_a_serve_run() -> None:
    run = SimpleNamespace(
        kind="not-installed+serve:run",
        spec=SimpleNamespace(task="not-installed+serve://project/function:function-id"),
    )

    assert RunServeProcessor.is_serve(run) is False


def _network(monkeypatch, answers: bool) -> SimpleNamespace:
    """Fake requests: the service answers directly or not; and the proxy of the client."""
    options = Mock() if answers else Mock(side_effect=serve_module.requests.ConnectionError("unknown host"))
    request = Mock()
    context = Mock()
    monkeypatch.setattr(serve_module.requests, "options", options)
    monkeypatch.setattr(serve_module.requests, "request", request)
    monkeypatch.setattr(serve_module, "get_context", Mock(return_value=context))
    return SimpleNamespace(options=options, request=request, proxy=context.client.proxy_request)


@pytest.mark.parametrize(
    ("method", "path", "kwargs", "expected"),
    [
        (None, None, {"json": {"inputs": []}}, ("POST", "http://model.ns:8080")),
        (None, "/v2/infer", {}, ("GET", "http://model.ns:8080/v2/infer")),
        ("DELETE", "v2/infer", {}, ("DELETE", "http://model.ns:8080/v2/infer")),
    ],
)
def test_invoke_calls_the_service_directly_when_it_answers(monkeypatch, method, path, kwargs, expected) -> None:
    network = _network(monkeypatch, answers=True)

    result = RunServeProcessor(Mock()).invoke(_serve_run({"url": "model.ns:8080"}), method, path, **kwargs)

    assert result is network.request.return_value
    network.options.assert_called_once_with(expected[1], timeout=serve_module.SERVICE_PROBE_TIMEOUT)
    network.request.assert_called_once_with(*expected, **kwargs)
    network.proxy.assert_not_called()


def test_invoke_goes_through_the_proxy_when_the_service_does_not_answer(monkeypatch) -> None:
    # From outside the cluster the service host does not resolve.
    network = _network(monkeypatch, answers=False)

    result = RunServeProcessor(Mock()).invoke(
        _serve_run({"url": "model.ns:8080"}), None, "/v2/infer", json={"inputs": []}
    )

    assert result is network.proxy.return_value
    network.proxy.assert_called_once_with("model.ns:8080", "POST", "/v2/infer", json={"inputs": []})
    network.request.assert_not_called()


@pytest.mark.parametrize("answers", [True, False])
def test_invoke_probes_the_service_once_per_run(monkeypatch, answers) -> None:
    # A host that resolves but drops packets made every call wait for the
    # probe timeout before going through the proxy.
    network = _network(monkeypatch, answers=answers)
    processor = RunServeProcessor(Mock())
    run = _serve_run({"url": "model.ns:8080"})

    processor.invoke(run, path="/a")
    processor.invoke(run, path="/b")

    assert network.options.call_count == 1
    assert (network.request if answers else network.proxy).call_count == 2


def test_invoke_probes_again_when_the_service_changes(monkeypatch) -> None:
    network = _network(monkeypatch, answers=True)
    processor = RunServeProcessor(Mock())
    run = _serve_run({"url": "model.ns:8080"})

    processor.invoke(run)
    run.status.service = {"url": "model-2.ns:8080"}
    processor.invoke(run)

    assert network.options.call_count == 2


def test_invoke_without_a_service_url_raises() -> None:
    with pytest.raises(EntityError, match="Run run-id has no service url"):
        RunServeProcessor(Mock()).invoke(_serve_run())
