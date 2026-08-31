from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from digitalhub.entities._commons.enums import State
from digitalhub.entities.run._base.entity import Run
from digitalhub.utils.exceptions import EntityError


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
    run.save = Mock()
    context = Mock()
    run._context = Mock(return_value=context)

    with pytest.raises(EntityError, match="not in a state to run"):
        run.start_execution()

    context.set_run.assert_not_called()


def test_start_execution_rolls_back_registration_when_state_save_fails() -> None:
    run = object.__new__(Run)
    run.status = SimpleNamespace(state=State.BUILT.value)
    run.local_execution = Mock(return_value=True)
    run.save = Mock(side_effect=RuntimeError("save failed"))
    context = Mock()
    run._context = Mock(return_value=context)

    with pytest.raises(RuntimeError, match="save failed"):
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
    run.save = Mock(return_value=run)
    runtime = Mock()
    runtime.run.return_value = {"state": "RUNTIME"}
    run._get_runtime = Mock(return_value=runtime)

    result = run.run()

    assert result is run
    run.set_status.assert_called_once_with({"state": expected_state})
