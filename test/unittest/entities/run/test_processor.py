# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from threading import current_thread
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities.run._base.processor as run_processor_module
from digitalhub.entities._commons.enums import State
from digitalhub.entities.log._base.entity import Log
from digitalhub.entities.run._base.processor import RunProcessor
from digitalhub.entities.run._base.spec import RunSpec
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.exceptions import EntityError
from digitalhub.utils.generic_utils import encode_string


def _context(name: str = "project") -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _executable() -> Mock:
    executable = Mock()
    executable.ENTITY_TYPE = "function"
    executable.name = "function"
    executable.project = "project"
    executable.to_dict.return_value = {"kind": "function"}
    return executable


def test_execute_builds_and_runs_local_run_in_caller_thread() -> None:
    processor = RunProcessor(Mock())
    run = Mock()
    run.local_execution.return_value = True
    processor.build = Mock()
    processor.run = Mock(side_effect=lambda _run: current_thread())
    processor.wait = Mock()

    result = processor.execute(run, wait=True)

    assert result is current_thread()
    processor.build.assert_called_once_with(run)
    processor.run.assert_called_once_with(run)
    processor.wait.assert_not_called()


def test_execute_returns_backend_run_without_waiting() -> None:
    processor = RunProcessor(Mock())
    run = Mock()
    run.local_execution.return_value = False
    processor.build = Mock()
    processor.run = Mock()
    processor.wait = Mock()

    assert processor.execute(run) is run

    processor.build.assert_not_called()
    processor.run.assert_not_called()
    processor.wait.assert_not_called()


def test_execute_waits_for_backend_run_when_requested() -> None:
    processor = RunProcessor(Mock())
    run = Mock()
    run.local_execution.return_value = False
    waited_run = Mock()
    run.wait.return_value = waited_run

    assert processor.execute(run, wait=True, log_info=False) is waited_run

    run.wait.assert_called_once_with(log_info=False)


def test_get_executable_reads_reference_through_crud(monkeypatch) -> None:
    executable = Mock()
    executable.to_dict.return_value = {"kind": "python-function"}
    crud_processor = Mock()
    crud_processor.read_context_entity.return_value = executable
    processor = RunProcessor(crud_processor)
    monkeypatch.setattr(
        run_processor_module.entity_factory,
        "get_executable_kind",
        Mock(return_value="python-function"),
    )
    monkeypatch.setattr(run_processor_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="function"))
    run = SimpleNamespace(
        kind="python-run",
        project="project",
        spec=SimpleNamespace(function="python-function://project/model:version"),
    )

    result = processor.get_executable(run)

    assert result == {"kind": "python-function"}
    crud_processor.read_context_entity.assert_called_once_with(
        "model",
        entity_type="function",
        project="project",
        entity_id="version",
    )


def test_get_task_reads_unversioned_reference_through_crud() -> None:
    task = Mock()
    task.to_dict.return_value = {"kind": "python-task"}
    crud_processor = Mock()
    crud_processor.read_unversioned_entity.return_value = task
    processor = RunProcessor(crud_processor)
    run = SimpleNamespace(project="project", spec=SimpleNamespace(task="task://project/task-id"))

    result = processor.get_task(run)

    assert result == {"kind": "python-task"}
    crud_processor.read_unversioned_entity.assert_called_once_with(
        "task-id",
        entity_type="task",
        project="project",
    )


def test_build_preserves_fields_from_runtime_merge(monkeypatch) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.update_context_entity = Mock()
    run = SimpleNamespace(
        id="run-id",
        kind="python+run",
        project="project",
        spec=RunSpec(task="task://project/task-id"),
        status=SimpleNamespace(state=State.CREATED.value),
        local_execution=Mock(return_value=True),
        to_dict=Mock(return_value={"spec": {"task": "task://project/task-id"}}),
    )
    processor.get_executable = Mock(return_value={"spec": {"function": "function-ref"}})
    processor.get_task = Mock(return_value={"spec": {"instructions": ["build"]}})
    runtime = Mock()
    runtime.build.return_value = {
        "task": "task://project/task-id",
        "function": "function-ref",
        "future_backend_field": "preserved",
    }
    monkeypatch.setattr(
        run_processor_module.runtime_factory,
        "build_runtime",
        Mock(return_value=runtime),
    )

    processor.build(run)

    assert run.spec.future_backend_field == "preserved"
    assert run.status.state == State.BUILT.value
    processor.crud_processor.update_context_entity.assert_called_once_with(run)


def test_wait_returns_without_sleep_for_terminal_state(monkeypatch) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock(
        side_effect=lambda run: setattr(run.status, "state", State.COMPLETED.value)
    )
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value),
    )
    sleep = Mock()
    clock_values = iter([10.0, 10.25])
    monkeypatch.setattr(
        run_processor_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    assert processor.wait(run, log_info=False) is run

    processor.crud_processor.refresh_context_entity.assert_called_once_with(run)
    sleep.assert_not_called()


def test_wait_sleeps_only_between_polls_and_times_out(monkeypatch) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock()
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value),
    )
    sleep = Mock()
    clock_values = iter([0.0, 0.0, 1.0, 2.0])
    monkeypatch.setattr(
        run_processor_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    with pytest.raises(TimeoutError, match="Run run-id did not finish within 2s"):
        processor.wait(run, log_info=False, timeout=2, poll_interval=1)

    assert processor.crud_processor.refresh_context_entity.call_count == 3
    assert sleep.call_args_list == [call(1), call(1)]


def test_wait_limits_sleep_to_remaining_timeout(monkeypatch) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock()
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value),
    )
    sleep = Mock()
    clock_values = iter([0.0, 0.0, 1.0, 1.5])
    monkeypatch.setattr(
        run_processor_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    with pytest.raises(TimeoutError):
        processor.wait(run, log_info=False, timeout=1.5, poll_interval=1)

    assert sleep.call_args_list == [call(1), call(0.5)]


@pytest.mark.parametrize(
    ("timeout", "poll_interval"),
    [(-1, 1), (None, 0)],
)
def test_wait_rejects_invalid_timing_values(timeout, poll_interval) -> None:
    processor = RunProcessor(Mock())
    run = SimpleNamespace(refresh=Mock())

    with pytest.raises(ValueError):
        processor.wait(run, timeout=timeout, poll_interval=poll_interval)

    run.refresh.assert_not_called()


def test_build_of_a_local_run_starts_only_from_created(monkeypatch) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.update_context_entity = Mock()
    build_runtime = Mock()
    monkeypatch.setattr(run_processor_module.runtime_factory, "build_runtime", build_runtime)
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.COMPLETED.value),
        local_execution=Mock(return_value=True),
    )

    with pytest.raises(EntityError, match="cannot go from COMPLETED to BUILT"):
        processor.build(run)

    build_runtime.assert_not_called()
    processor.crud_processor.update_context_entity.assert_not_called()


def test_run_marks_a_local_run_as_error_when_setup_fails() -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock()
    processor.crud_processor.update_context_entity = Mock()
    processor.start_execution = Mock()
    processor.end_execution = Mock()
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value, message=None),
        local_execution=Mock(return_value=True),
        _setup_execution=Mock(side_effect=RuntimeError("setup failed")),
    )

    with pytest.raises(RuntimeError, match="setup failed"):
        processor.run(run)

    processor.end_execution.assert_called_once_with(run)
    assert run.status.state == State.ERROR.value
    assert run.status.message == "setup failed"
    processor.crud_processor.update_context_entity.assert_called_once_with(run)


def test_run_ends_execution_when_runtime_fails(monkeypatch) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock()
    processor.crud_processor.update_context_entity = Mock()
    processor.start_execution = Mock()
    processor.end_execution = Mock()
    run = SimpleNamespace(
        id="run-id",
        kind="python+run",
        project="project",
        status=SimpleNamespace(state=State.RUNNING.value, message=None),
        _setup_execution=Mock(),
        local_execution=Mock(return_value=True),
        to_dict=Mock(return_value={}),
    )
    runtime = Mock()
    runtime.run.side_effect = RuntimeError("runtime failed")
    monkeypatch.setattr(
        run_processor_module.runtime_factory,
        "build_runtime",
        Mock(return_value=runtime),
    )

    with pytest.raises(RuntimeError, match="runtime failed"):
        processor.run(run)

    processor.end_execution.assert_called_once_with(run)
    assert run.status.state == State.ERROR.value
    assert run.status.message == "runtime failed"


@pytest.mark.parametrize("state", [State.CREATED.value, State.STOPPED.value, State.COMPLETED.value])
def test_start_execution_validates_state_before_registration(state: str) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.update_context_entity = Mock()
    context = Mock()
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=state),
        local_execution=Mock(return_value=True),
        _context=Mock(return_value=context),
    )

    with pytest.raises(EntityError, match=f"cannot go from {state} to READY"):
        processor.start_execution(run)

    context.set_run.assert_not_called()
    processor.crud_processor.update_context_entity.assert_not_called()


def test_start_execution_rolls_back_registration() -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.update_context_entity = Mock(side_effect=RuntimeError("update failed"))
    context = Mock()
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.BUILT.value),
        local_execution=Mock(return_value=True),
        _context=Mock(return_value=context),
    )

    with pytest.raises(RuntimeError, match="update failed"):
        processor.start_execution(run)

    context.set_run.assert_called_once_with(run)
    context.unset_run.assert_called_once_with()


@pytest.mark.parametrize(
    ("local_execution", "expected_state"),
    [
        (False, State.RUNNING.value),
        (True, State.COMPLETED.value),
    ],
)
def test_run_state_precedence(monkeypatch, local_execution: bool, expected_state: str) -> None:
    processor = RunProcessor(Mock())
    processor.crud_processor.refresh_context_entity = Mock()
    processor.crud_processor.update_context_entity = Mock()
    processor.start_execution = Mock()
    processor.end_execution = Mock()
    run = SimpleNamespace(
        id="run-id",
        kind="python+run",
        project="project",
        status=SimpleNamespace(
            state=State.RUNNING.value,
            to_dict=Mock(return_value={"state": State.RUNNING.value}),
        ),
        _setup_execution=Mock(),
        local_execution=Mock(return_value=local_execution),
        to_dict=Mock(return_value={}),
    )
    runtime = Mock()
    runtime.run.return_value = {"state": State.COMPLETED.value}
    run.set_status = Mock(side_effect=lambda status: setattr(run, "status", SimpleNamespace(state=status["state"])))
    monkeypatch.setattr(
        run_processor_module.runtime_factory,
        "build_runtime",
        Mock(return_value=runtime),
    )

    result = processor.run(run)

    assert result is run
    run.set_status.assert_called_once_with({"state": expected_state})
    assert run.status.state == expected_state


def test_read_logs_builds_logs_and_decodes_content(monkeypatch) -> None:
    client = Mock()
    context = SimpleNamespace(client=client)
    logs = [
        {
            "project": "project",
            "name": "run-log",
            "id": "log-id",
            "spec": {"run": "run-id"},
            "content": encode_string("run finished"),
        },
        {
            "project": "project",
            "name": "other-log",
            "id": "other-id",
            "spec": {"run": "run-id"},
        },
    ]
    client.execute.return_value = logs
    monkeypatch.setattr(run_processor_module, "get_context", Mock(return_value=context))
    run = SimpleNamespace(project="project", ENTITY_TYPE="run", id="run-id")

    processor = RunProcessor(Mock())
    result = processor.read_logs(run, as_entity=True, state="READY")

    assert all(isinstance(log, Log) for log in result)
    assert [log.kind for log in result] == ["log", "log"]
    assert [log.text for log in result] == ["run finished", None]
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.LOGS_READ,
            target=ContextEntityTarget("project", "run", "run-id"),
            options=LogsOptions(state="READY"),
        )
    )

    client.reset_mock()
    client.execute.return_value = [
        {
            "project": "project",
            "name": "text-log",
            "id": "text-log-id",
            "spec": {"run": "run-id"},
            "content": encode_string("text output"),
        }
    ]

    assert processor.read_logs(run) == ["text output"]
