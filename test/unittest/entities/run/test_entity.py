# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities.run._base.entity as run_entity_module
from digitalhub.entities._commons.enums import State
from digitalhub.entities.run._base.entity import Run
from digitalhub.utils.exceptions import EntityError


def test_wait_returns_without_sleep_when_refresh_reports_terminal_state(monkeypatch) -> None:
    run = object.__new__(Run)
    run.id = "run-id"
    run.status = SimpleNamespace(state=State.RUNNING.value)
    run.refresh = Mock(side_effect=lambda: setattr(run.status, "state", State.COMPLETED.value))
    sleep = Mock()
    clock_values = iter([10.0, 10.25])
    monkeypatch.setattr(
        run_entity_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    assert run.wait(log_info=False) is run

    run.refresh.assert_called_once_with()
    sleep.assert_not_called()


def test_wait_sleeps_only_between_polls_and_times_out(monkeypatch) -> None:
    run = object.__new__(Run)
    run.id = "run-id"
    run.status = SimpleNamespace(state=State.RUNNING.value)
    run.refresh = Mock(return_value=run)
    sleep = Mock()
    clock_values = iter([0.0, 0.0, 1.0, 2.0])
    monkeypatch.setattr(
        run_entity_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    with pytest.raises(TimeoutError, match="Run run-id did not finish within 2s"):
        run.wait(log_info=False, timeout=2, poll_interval=1)

    assert run.refresh.call_count == 3
    assert sleep.call_args_list == [call(1), call(1)]


def test_wait_limits_sleep_to_remaining_timeout(monkeypatch) -> None:
    run = object.__new__(Run)
    run.id = "run-id"
    run.status = SimpleNamespace(state=State.RUNNING.value)
    run.refresh = Mock(return_value=run)
    sleep = Mock()
    clock_values = iter([0.0, 0.0, 1.0, 1.5])
    monkeypatch.setattr(
        run_entity_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    with pytest.raises(TimeoutError):
        run.wait(log_info=False, timeout=1.5, poll_interval=1)

    assert sleep.call_args_list == [call(1), call(0.5)]


@pytest.mark.parametrize(
    ("timeout", "poll_interval"),
    [(-1, 1), (None, 0)],
)
def test_wait_rejects_invalid_timing_values(timeout, poll_interval) -> None:
    run = object.__new__(Run)
    run.refresh = Mock()

    with pytest.raises(ValueError):
        run.wait(timeout=timeout, poll_interval=poll_interval)

    run.refresh.assert_not_called()


def test_run_ends_execution_when_setup_fails() -> None:
    run = object.__new__(Run)
    run.refresh = Mock(return_value=run)
    run.start_execution = Mock()
    run._setup_execution = Mock(side_effect=RuntimeError("setup failed"))
    run.end_execution = Mock()

    with pytest.raises(RuntimeError, match="setup failed"):
        run.run()

    run.end_execution.assert_called_once_with()


def test_start_execution_validates_state_before_registering_run() -> None:
    run = object.__new__(Run)
    run.status = SimpleNamespace(state=State.CREATED.value)
    run.local_execution = Mock(return_value=True)
    run.update = Mock()
    context = Mock()
    run._context = Mock(return_value=context)

    with pytest.raises(EntityError, match="not in a state to run"):
        run.start_execution()

    context.set_run.assert_not_called()


def test_start_execution_rolls_back_registration_when_state_update_fails() -> None:
    run = object.__new__(Run)
    run.status = SimpleNamespace(state=State.BUILT.value)
    run.local_execution = Mock(return_value=True)
    run.update = Mock(side_effect=RuntimeError("update failed"))
    context = Mock()
    run._context = Mock(return_value=context)

    with pytest.raises(RuntimeError, match="update failed"):
        run.start_execution()

    context.set_run.assert_called_once_with(run)
    context.unset_run.assert_called_once_with()


@pytest.mark.parametrize(
    ("local_execution", "expected_state"),
    [
        (False, "BACKEND"),
        (True, "RUNTIME"),
    ],
)
def test_run_state_precedence(local_execution: bool, expected_state: str) -> None:
    run = object.__new__(Run)
    run.status = SimpleNamespace(to_dict=Mock(return_value={"state": "BACKEND"}))
    run.refresh = Mock(return_value=run)
    run.start_execution = Mock()
    run._setup_execution = Mock()
    run.end_execution = Mock()
    run.local_execution = Mock(return_value=local_execution)
    run.to_dict = Mock(return_value={})
    run.set_status = Mock()
    run.update = Mock(return_value=run)
    runtime = Mock()
    runtime.run.return_value = {"state": "RUNTIME"}
    run._get_runtime = Mock(return_value=runtime)

    result = run.run()

    assert result is run
    run.set_status.assert_called_once_with({"state": expected_state})
