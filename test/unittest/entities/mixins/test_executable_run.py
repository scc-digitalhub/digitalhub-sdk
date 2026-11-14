# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.executable.run as run_module
from digitalhub.entities._commons.enums import Relationship
from digitalhub.entities._mixin.executable.run import ExecutableRunMixin
from digitalhub.entities.function._base.entity import Function
from digitalhub.entities.workflow._base.entity import Workflow
from digitalhub.factory.entity import entity_factory
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


def test_get_run_matches_id_or_key_and_rejects_other_executables() -> None:
    executable = StubExecutable()
    executable._list_runs = Mock(
        return_value=[
            _run(executable, "run-id", "run-key", executable._get_executable_string()),
            _run(executable, "other-id", "other-key", "python://project/other:other-id"),
        ]
    )

    matching_run = executable._list_runs.return_value[0]
    assert executable.get_run("run-id") is matching_run
    assert executable.get_run("run-key") is matching_run

    with pytest.raises(EntityError, match="Run 'other-id' does not exist"):
        executable.get_run("other-id")


def test_list_runs_forwards_filters() -> None:
    executable = StubExecutable()
    executable._list_runs = Mock(return_value=[])

    assert executable.list_runs(q="query", task="task-key", action="execute") == []
    executable._list_runs.assert_called_once_with(
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


def test_list_runs_filters_by_executable(monkeypatch) -> None:
    executable = StubExecutable()
    list_runs = Mock(return_value=["run"])
    monkeypatch.setattr(run_module, "list_runs", list_runs)

    assert executable._list_runs(state="RUNNING") == ["run"]

    list_runs.assert_called_once_with(
        "project",
        state="RUNNING",
        function="python://project/function:function-id",
    )


@pytest.mark.parametrize(
    ("executable_class", "task_kwargs"),
    [(Function, {}), (Workflow, {"local_execution": False})],
)
def test_function_and_workflow_runs_append_extensions_consistently(
    monkeypatch, executable_class, task_kwargs: dict
) -> None:
    executable = object.__new__(executable_class)
    executable.kind = "python"
    executable.key = "executable-key"

    existing_extensions = [{"name": "task-extension"}]
    additional_extensions = [{"name": "run-extension"}]
    run = Mock()
    run.extensions = existing_extensions.copy()
    run.local_execution.return_value = False
    task = Mock()
    task.run.return_value = run
    executable._get_or_create_task = Mock(return_value=task)
    monkeypatch.setattr(entity_factory, "get_run_kind_from_action", Mock(return_value="python+run"))

    assert executable.run("execute", extensions=additional_extensions) is run

    task.run.assert_called_once_with("python+run", save=False, **task_kwargs)
    assert run.extensions == existing_extensions + additional_extensions
    run.add_relationship.assert_called_once_with(Relationship.RUN_OF.value, "executable-key")
    run.save.assert_called_once_with()
