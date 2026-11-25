# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import threading
from concurrent.futures import ThreadPoolExecutor, wait
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
    first_project = SimpleNamespace(
        name="project",
        spec=SimpleNamespace(config={"profile": "old"}, source=str(tmp_path / "old")),
    )
    context = builder.build(first_project)
    run = SimpleNamespace(key="run-key", id="run-id")
    context.set_run(run)
    context.logged["artifact"] = "artifact-key"

    updated_root = tmp_path / "updated"
    updated_project = SimpleNamespace(
        name="project",
        spec=SimpleNamespace(config={"profile": "new"}, source=str(updated_root)),
    )

    assert builder.build(updated_project) is context
    assert context.config == {"profile": "new"}
    assert context.root == Path(updated_root)
    assert context.run is run
    assert context.is_running
    assert context.logged == {"artifact": "artifact-key"}
    assert not updated_root.exists()


# Time other builds are given to overtake a paused one. With the lock they stay
# blocked, so this only bounds the test; it never decides it.
OVERTAKE_WINDOW = 0.5
JOIN_TIMEOUT = 5


def test_concurrent_builds_return_one_initialized_context(monkeypatch, tmp_path) -> None:
    # The first build pauses inside Context.__init__. Without the lock the
    # other builds found the registered but uninitialized instance and
    # returned it, so reading its name failed.
    builder = ContextBuilder()
    project = SimpleNamespace(name="project", spec=SimpleNamespace(config={}, source=str(tmp_path)))
    paused = threading.Event()
    resume = threading.Event()
    initialize = Context.__init__

    def paused_initialize(context, current_project) -> None:
        if not paused.is_set():
            paused.set()
            resume.wait(JOIN_TIMEOUT)
        initialize(context, current_project)

    monkeypatch.setattr(Context, "__init__", paused_initialize)

    def build() -> tuple[Context, str]:
        context = builder.build(project)
        return context, context.name

    with ThreadPoolExecutor(max_workers=8) as pool:
        first = pool.submit(build)
        assert paused.wait(JOIN_TIMEOUT)
        others = [pool.submit(build) for _ in range(7)]
        wait(others, timeout=OVERTAKE_WINDOW)
        resume.set()
        results = [future.result(timeout=JOIN_TIMEOUT) for future in (first, *others)]

    context = builder.get("project")
    assert results == [(context, "project")] * 8
