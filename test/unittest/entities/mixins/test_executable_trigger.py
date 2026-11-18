# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

from digitalhub.entities._mixin.executable.trigger import ExecutableTriggerMixin


class StubExecutable(ExecutableTriggerMixin):
    pass


def test_trigger_delegates_to_executable_processor(monkeypatch) -> None:
    executable = StubExecutable()
    create_trigger = Mock(return_value="trigger")
    monkeypatch.setattr(
        "digitalhub.entities._mixin.executable.trigger.executable_processor.create_trigger",
        create_trigger,
    )

    result = executable.trigger(
        action="execute",
        kind="lifecycle",
        name="on-demand",
        template={"custom": "value"},
        description="A trigger",
    )

    assert result == "trigger"
    create_trigger.assert_called_once_with(
        executable,
        "execute",
        "lifecycle",
        "on-demand",
        template={"custom": "value"},
        description="A trigger",
    )


def test_get_trigger_delegates_to_executable_processor(monkeypatch) -> None:
    executable = StubExecutable()
    get_trigger = Mock(return_value="trigger")
    monkeypatch.setattr(
        "digitalhub.entities._mixin.executable.trigger.executable_processor.get_executable_trigger",
        get_trigger,
    )

    assert executable.get_trigger("trigger-id") == "trigger"
    get_trigger.assert_called_once_with(executable, "trigger-id")


def test_list_triggers_delegates_filters(monkeypatch) -> None:
    executable = StubExecutable()
    list_triggers = Mock(return_value=[])
    monkeypatch.setattr(
        "digitalhub.entities._mixin.executable.trigger.executable_processor.list_executable_triggers",
        list_triggers,
    )

    assert executable.list_triggers(q="query", task="task-key") == []
    list_triggers.assert_called_once_with(
        executable,
        q="query",
        name=None,
        kind=None,
        user=None,
        created=None,
        updated=None,
        versions=None,
        task="task-key",
    )
