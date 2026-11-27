# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._mixin.executable.build import ExecutableBuildMixin


class RecordingExecutable(ExecutableBuildMixin):
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def run(self, action: str, **kwargs) -> str:
        self.calls.append((action, kwargs))
        return "build-run"


def test_build_executes_the_build_action_through_run() -> None:
    # Through run(), not the processor: a runtime that overrides run(), like
    # python with its version check, applies the override to builds too.
    executable = RecordingExecutable()

    result = executable.build(extensions=[{"name": "ext"}], instructions=["pip install x"])

    assert result == "build-run"
    assert executable.calls == [
        (
            "build",
            {"wait": True, "log_info": True, "extensions": [{"name": "ext"}], "instructions": ["pip install x"]},
        )
    ]
