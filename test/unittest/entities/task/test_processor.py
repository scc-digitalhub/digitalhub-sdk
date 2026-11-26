# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities.task._base.processor as task_processor_module
from digitalhub.entities.task._base.processor import TaskProcessor


def _context(name: str = "project") -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _executable() -> Mock:
    executable = Mock()
    executable.ENTITY_TYPE = "function"
    executable.name = "function"
    executable.project = "project"
    executable.to_dict.return_value = {"kind": "function"}
    return executable


def test_build_run_adds_executable_reference(monkeypatch) -> None:
    crud_processor = Mock()
    processor = TaskProcessor(crud_processor)
    task = SimpleNamespace(
        kind="python+job",
        project="project",
        spec=SimpleNamespace(function="function-ref"),
        _get_task_string=Mock(return_value="task-ref"),
    )
    run = Mock()
    monkeypatch.setattr(
        task_processor_module.entity_factory, "get_executable_kind", Mock(return_value="python-function")
    )
    monkeypatch.setattr(
        task_processor_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="function")
    )
    build_entity = Mock(return_value=run)
    monkeypatch.setattr(task_processor_module.entity_factory, "build_entity_from_params", build_entity)

    result = processor.build_run(task, "python+run", save=False, labels=["run"])

    assert result is run
    build_entity.assert_called_once_with(
        project="project",
        task="task-ref",
        kind="python+run",
        entity_type="run",
        function="function-ref",
        labels=["run"],
    )
