# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from types import SimpleNamespace

import pytest

from digitalhub.context.builder import ContextBuilder
from digitalhub.context.context import Context
from digitalhub.utils.exceptions import ContextError


def test_build_rolls_back_failed_context_and_can_retry(monkeypatch) -> None:
    builder = ContextBuilder()
    project = SimpleNamespace(name="project")
    initialization_count = 0

    def initialize(context, current_project) -> None:
        nonlocal initialization_count
        initialization_count += 1
        assert builder.get(current_project.name) is context
        if initialization_count == 1:
            raise RuntimeError("init failed")
        context.name = current_project.name

    monkeypatch.setattr(Context, "__init__", initialize)

    with pytest.raises(RuntimeError, match="init failed"):
        builder.build(project)

    with pytest.raises(ContextError, match="not found"):
        builder.get(project.name)

    context = builder.build(project)

    assert context.name == project.name
    assert initialization_count == 2


def test_build_updates_cached_context_without_resetting_run_state(tmp_path) -> None:
    builder = ContextBuilder()
    first_client = object()
    first_project = SimpleNamespace(
        name="project",
        _client=first_client,
        spec=SimpleNamespace(config={"profile": "old"}, source=str(tmp_path / "old")),
    )
    context = builder.build(first_project)
    run = SimpleNamespace(key="run-key", id="run-id")
    context.set_run(run)
    context.logged["artifact"] = "artifact-key"

    updated_client = object()
    updated_root = tmp_path / "updated"
    updated_project = SimpleNamespace(
        name="project",
        _client=updated_client,
        spec=SimpleNamespace(config={"profile": "new"}, source=str(updated_root)),
    )

    assert builder.build(updated_project) is context
    assert context.client is updated_client
    assert context.config == {"profile": "new"}
    assert context.root == Path(updated_root)
    assert context.run is run
    assert context.is_running
    assert context.logged == {"artifact": "artifact-key"}
    assert not updated_root.exists()
