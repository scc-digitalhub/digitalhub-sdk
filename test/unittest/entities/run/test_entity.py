# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import digitalhub.entities.run._base.entity as run_entity_module
from digitalhub.entities.run._base.entity import Run


def test_build_delegates_to_executable_processor(monkeypatch) -> None:
    run = object.__new__(Run)
    build_run = Mock()
    monkeypatch.setattr(run_entity_module.executable_processor, "build_run", build_run)

    assert run.build() is None
    build_run.assert_called_once_with(run)


def test_run_delegates_to_executable_processor(monkeypatch) -> None:
    run = object.__new__(Run)
    executed = Mock()
    run_run = Mock(return_value=executed)
    monkeypatch.setattr(run_entity_module.executable_processor, "run_run", run_run)

    assert run.run() is executed
    run_run.assert_called_once_with(run)


def test_wait_delegates_to_executable_processor(monkeypatch) -> None:
    run = object.__new__(Run)
    waited = Mock()
    wait_run = Mock(return_value=waited)
    monkeypatch.setattr(run_entity_module.executable_processor, "wait_run", wait_run)

    assert run.wait(log_info=False, timeout=10, poll_interval=2) is waited
    wait_run.assert_called_once_with(
        run,
        log_info=False,
        timeout=10,
        poll_interval=2,
    )


def test_logs_delegates_and_returns_selected_representation(monkeypatch) -> None:
    run = object.__new__(Run)
    read_run_logs = Mock(side_effect=[["first", "second"], [Mock()]])
    monkeypatch.setattr(run_entity_module.executable_processor, "read_run_logs", read_run_logs)

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
    monkeypatch.setattr(run_entity_module.executable_processor, "start_run_execution", start)
    monkeypatch.setattr(run_entity_module.executable_processor, "end_run_execution", end)

    run.start_execution()
    run.end_execution()

    start.assert_called_once_with(run)
    end.assert_called_once_with(run)
