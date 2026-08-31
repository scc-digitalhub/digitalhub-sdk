from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.entities.run._base.entity import Run


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
    run.save = Mock(return_value=run)
    runtime = Mock()
    runtime.run.return_value = {"state": "RUNTIME"}
    run._get_runtime = Mock(return_value=runtime)

    result = run.run()

    assert result is run
    run.set_status.assert_called_once_with({"state": expected_state})
