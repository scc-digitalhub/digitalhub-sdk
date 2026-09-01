from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._mixin.executable.run as run_module
from digitalhub.entities._mixin.executable.run import ExecutableRunMixin
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
