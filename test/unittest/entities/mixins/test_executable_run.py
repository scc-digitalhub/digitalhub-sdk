# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.executable.mixin as executable_mixin_module
from digitalhub.entities._mixin.executable.run import ExecutableRunMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities.function._base.entity import Function
from digitalhub.entities.workflow._base.entity import Workflow
from digitalhub.utils.exceptions import EntityError


class StubExecutable(ExecutableRunMixin):
    ENTITY_TYPE = "function"
    project = "project"
    kind = "python"
    name = "function"
    id = "function-id"
    key = "function-key"


def _run(executable: StubExecutable, run_id: str, run_key: str, function: str):
    return SimpleNamespace(
        id=run_id,
        key=run_key,
        spec=SimpleNamespace(function=function),
    )


def test_new_run_delegates_to_executable_processor(monkeypatch) -> None:
    executable = StubExecutable()
    run = Mock()
    create_run = Mock(return_value=run)
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        "create_run",
        create_run,
    )

    assert executable.new_run("execute", extensions=[{"name": "extension"}]) is run
    create_run.assert_called_once_with(
        executable,
        "execute",
        extensions=[{"name": "extension"}],
    )


def test_get_run_matches_id_or_key_and_rejects_other_executables(monkeypatch) -> None:
    executable = StubExecutable()
    matching_run = _run(executable, "run-id", "run-key", executable._get_executable_string())
    get_run = Mock(
        side_effect=[
            matching_run,
            matching_run,
            EntityError("Run 'other-id' does not exist or does not belong to this executable."),
        ]
    )
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        "get_executable_run",
        get_run,
    )

    assert executable.get_run("run-id") is matching_run
    assert executable.get_run("run-key") is matching_run

    with pytest.raises(EntityError, match="Run 'other-id' does not exist"):
        executable.get_run("other-id")


def test_list_runs_forwards_filters(monkeypatch) -> None:
    executable = StubExecutable()
    list_runs = Mock(return_value=[])
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        "list_executable_runs",
        list_runs,
    )

    assert executable.list_runs(q="query", task="task-key", action="execute") == []
    list_runs.assert_called_once_with(
        executable,
        q="query",
        name=None,
        kind=None,
        user=None,
        state=None,
        created=None,
        updated=None,
        task="task-key",
        action="execute",
    )


def test_delete_run_delegates_to_executable_processor(monkeypatch) -> None:
    executable = StubExecutable()
    delete_run = Mock(return_value={"deleted": True})
    monkeypatch.setattr(
        ContextEntityExecutableProcessor,
        "delete_executable_run",
        delete_run,
    )

    assert executable.delete_run("run-id") == {"deleted": True}
    delete_run.assert_called_once_with(executable, "run-id")


@pytest.mark.parametrize(
    ("executable_class", "task_kwargs"),
    [(Function, {}), (Workflow, {})],
)
def test_function_and_workflow_runs_append_extensions_consistently(
    monkeypatch, executable_class, task_kwargs: dict
) -> None:
    executable = object.__new__(executable_class)
    executable.kind = "python"
    executable.key = "executable-key"

    additional_extensions = [{"name": "run-extension"}]
    run = Mock()
    execute_executable = Mock(return_value=run)
    processor = Mock()
    processor.execute_executable = execute_executable
    monkeypatch.setattr(executable_mixin_module, "ContextEntityExecutableProcessor", Mock(return_value=processor))

    assert executable.run("execute", extensions=additional_extensions) is run

    execute_executable.assert_called_once_with(
        executable,
        "execute",
        wait=False,
        log_info=True,
        extensions=additional_extensions,
        **task_kwargs,
    )
