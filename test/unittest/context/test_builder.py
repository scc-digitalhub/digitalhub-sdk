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
