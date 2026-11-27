# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from digitalhub.entities.run._base.entity import (
    BuildRunMixin,
    EntityIORunMixin,
    ResultsRunMixin,
    Run,
    ServeRunMixin,
)
from digitalhub.entities.run._base.io_processor import RunIOProcessor
from digitalhub.entities.run._base.processor import RunProcessor
from digitalhub.entities.run._base.serve_processor import RunServeProcessor


def test_build_delegates_to_executable_processor(monkeypatch) -> None:
    run = object.__new__(Run)
    build_run = Mock()
    monkeypatch.setattr(RunProcessor, "build", build_run)

    assert run.build() is None
    build_run.assert_called_once_with(run)


def test_run_delegates_to_executable_processor(monkeypatch) -> None:
    run = object.__new__(Run)
    executed = Mock()
    run_run = Mock(return_value=executed)
    monkeypatch.setattr(RunProcessor, "run", run_run)

    assert run.run() is executed
    run_run.assert_called_once_with(run)


def test_wait_delegates_to_executable_processor(monkeypatch) -> None:
    run = object.__new__(Run)
    waited = Mock()
    wait_run = Mock(return_value=waited)
    monkeypatch.setattr(RunProcessor, "wait", wait_run)

    assert run.wait(log_info=False, timeout=10, poll_interval=2) is waited
    wait_run.assert_called_once_with(
        run,
        log_info=False,
        timeout=10,
        poll_interval=2,
    )


def test_invoke_of_a_serve_run_delegates_to_serve_processor(monkeypatch) -> None:
    run = object.__new__(type("ServeRun", (ServeRunMixin, Run), {}))
    response = Mock()
    invoke = Mock(return_value=response)
    monkeypatch.setattr(RunServeProcessor, "invoke", invoke)

    assert run.invoke(path="/v2/infer", json={"inputs": []}) is response
    invoke.assert_called_once_with(run, None, "/v2/infer", json={"inputs": []})


def test_inputs_and_outputs_delegate_to_io_processor(monkeypatch) -> None:
    run = object.__new__(type("IORun", (EntityIORunMixin, Run), {}))
    for method in ("inputs", "outputs", "output", "prepare_inputs"):
        monkeypatch.setattr(RunIOProcessor, method, Mock(return_value=method))

    assert run.inputs(as_dict=True) == "inputs"
    assert run.outputs(as_key=True) == "outputs"
    assert run.output("model", as_dict=True) == "output"
    run._setup_execution()

    RunIOProcessor.inputs.assert_called_once_with(run, as_dict=True)
    RunIOProcessor.outputs.assert_called_once_with(run, as_key=True, as_dict=False)
    RunIOProcessor.output.assert_called_once_with(run, "model", as_key=False, as_dict=True)
    RunIOProcessor.prepare_inputs.assert_called_once_with(run)


def test_results_come_from_the_status() -> None:
    run = object.__new__(type("ResultsRun", (ResultsRunMixin, Run), {}))
    run.status = Mock(results={"accuracy": 0.9})

    assert run.results() == {"accuracy": 0.9}
    assert run.result("accuracy") == 0.9
    assert run.result("missing") is None

    run.status = Mock(results=None)
    assert run.results() == {}


def test_image_of_a_build_run_comes_from_the_status_outputs() -> None:
    run = object.__new__(type("BuildRun", (BuildRunMixin, Run), {}))
    run.status = Mock(outputs={"image": "registry/image:tag"})

    assert run.image == "registry/image:tag"

    # Until the build publishes it.
    run.status = Mock(outputs=None)
    assert run.image is None


def test_logs_delegates_and_returns_selected_representation(monkeypatch) -> None:
    run = object.__new__(Run)
    read_run_logs = Mock(side_effect=[["first", "second"], [Mock()]])
    monkeypatch.setattr(RunProcessor, "read_logs", read_run_logs)

    assert run.logs() == ["first", "second"]
    assert isinstance(run.logs(as_entity=True), list)
    assert read_run_logs.call_count == 2
    assert read_run_logs.call_args_list == [
        ((run,), {"as_entity": False}),
        ((run,), {"as_entity": True}),
    ]


def test_execution_context_methods_delegate_for_compatibility(monkeypatch) -> None:
    run = object.__new__(Run)
    start = Mock()
    end = Mock()
    monkeypatch.setattr(RunProcessor, "start_execution", start)
    monkeypatch.setattr(RunProcessor, "end_execution", end)

    run.start_execution()
    run.end_execution()

    start.assert_called_once_with(run)
    end.assert_called_once_with(run)
