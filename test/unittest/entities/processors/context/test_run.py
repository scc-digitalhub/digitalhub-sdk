# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from threading import current_thread
from types import SimpleNamespace
from unittest.mock import Mock

import digitalhub.entities._processors.context.run as run_module
from digitalhub.entities._processors.context.run import ContextEntityRunProcessor
from digitalhub.entities.log._base.entity import Log
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.generic_utils import encode_string


def _context() -> tuple[SimpleNamespace, Mock, object]:
    client = Mock()
    context = SimpleNamespace(name="context-project", client=client)
    return context, client, object()


def test_read_run_logs_builds_logs_and_decodes_content(monkeypatch) -> None:
    context, client, _ = _context()
    logs = [
        {
            "project": "project",
            "name": "run-log",
            "id": "log-id",
            "spec": {"run": "run-id"},
            "content": encode_string("run finished"),
        },
        {
            "project": "project",
            "name": "other-log",
            "id": "other-id",
            "spec": {"run": "run-id"},
        },
    ]
    client.execute.return_value = logs
    monkeypatch.setattr(run_module, "get_context", Mock(return_value=context))

    result = ContextEntityRunProcessor().read_run_logs(
        "project",
        "run",
        "run-id",
        state="READY",
    )

    assert all(isinstance(log, Log) for log in result)
    assert [log.kind for log in result] == ["log", "log"]
    assert [log.text for log in result] == ["run finished", None]
    client.execute.assert_called_once_with(
        ClientOp(
            category=ApiType.CONTEXT,
            operation=BackendOp.LOGS_READ,
            target=ContextEntityTarget("project", "run", "run-id"),
            options=LogsOptions(state="READY"),
        )
    )


def test_get_run_executable_reads_reference_through_crud(monkeypatch) -> None:
    executable = Mock()
    executable.to_dict.return_value = {"kind": "python-function"}
    crud_processor = Mock()
    crud_processor.read_context_entity.return_value = executable
    monkeypatch.setattr(run_module.entity_factory, "get_executable_kind", Mock(return_value="python-function"))
    monkeypatch.setattr(run_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="function"))
    run = SimpleNamespace(
        kind="python-run",
        project="project",
        spec=SimpleNamespace(function="python-function://project/model:version"),
    )

    result = ContextEntityRunProcessor(crud_processor).get_run_executable(run)

    assert result == {"kind": "python-function"}
    crud_processor.read_context_entity.assert_called_once_with(
        "model",
        entity_type="function",
        project="project",
        entity_id="version",
    )


def test_get_run_task_reads_unversioned_reference_through_crud() -> None:
    task = Mock()
    task.to_dict.return_value = {"kind": "python-task"}
    crud_processor = Mock()
    crud_processor.read_unversioned_entity.return_value = task
    run = SimpleNamespace(project="project", spec=SimpleNamespace(task="task://project/task-id"))

    result = ContextEntityRunProcessor(crud_processor).get_run_task(run)

    assert result == {"kind": "python-task"}
    crud_processor.read_unversioned_entity.assert_called_once_with(
        "task-id",
        entity_type="task",
        project="project",
    )


def test_execute_run_builds_and_runs_local_run_in_caller_thread() -> None:
    run = Mock()
    run.local_execution.return_value = True
    run.run.side_effect = current_thread

    result = ContextEntityRunProcessor().execute_run(run, wait=True)

    assert result is current_thread()
    run.build.assert_called_once_with()
    run.run.assert_called_once_with()
    run.wait.assert_not_called()


def test_execute_run_returns_backend_run_without_waiting() -> None:
    run = Mock()
    run.local_execution.return_value = False

    assert ContextEntityRunProcessor().execute_run(run) is run

    run.build.assert_not_called()
    run.run.assert_not_called()
    run.wait.assert_not_called()


def test_execute_run_waits_for_backend_run_when_requested() -> None:
    run = Mock()
    run.local_execution.return_value = False
    waited_run = Mock()
    run.wait.return_value = waited_run

    assert ContextEntityRunProcessor().execute_run(run, wait=True, log_info=False) is waited_run

    run.wait.assert_called_once_with(log_info=False)


def test_execute_executable_creates_task_run_and_executes_it() -> None:
    executable = Mock()
    task = Mock()
    run = Mock()
    run.local_execution.return_value = False
    executable_processor = Mock()
    executable_processor.get_or_create_task.return_value = task
    executable_processor.create_run.return_value = run
    processor = ContextEntityRunProcessor(executable_processor=executable_processor)

    result = processor.execute_executable(
        executable,
        "execute",
        wait=False,
        extensions=[{"name": "extension"}],
        parameter="value",
    )

    assert result is run
    executable_processor.get_or_create_task.assert_called_once_with(executable, "execute")
    executable_processor.create_run.assert_called_once_with(
        executable,
        task,
        "execute",
        extensions=[{"name": "extension"}],
        parameter="value",
    )


def test_build_task_run_adds_executable_reference(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityRunProcessor(crud_processor)
    task = SimpleNamespace(
        kind="python+job",
        project="project",
        spec=SimpleNamespace(function="function-ref"),
        _get_task_string=Mock(return_value="task-ref"),
    )
    run = Mock()
    monkeypatch.setattr(run_module.entity_factory, "get_executable_kind", Mock(return_value="python-function"))
    monkeypatch.setattr(run_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="function"))
    processor.create_run = Mock(return_value=run)

    result = processor.build_task_run(task, "python+run", save=False, labels=["run"])

    assert result is run
    processor.create_run.assert_called_once_with(
        project="project",
        task="task-ref",
        kind="python+run",
        entity_type="run",
        save=False,
        function="function-ref",
        labels=["run"],
    )


def test_run_crud_operations_delegate_to_crud_processor() -> None:
    crud_processor = Mock()
    processor = ContextEntityRunProcessor(crud_processor)
    built = Mock()
    crud_processor.create_context_entity.return_value = built

    assert processor.create_run(save=True, project="project") is built
    crud_processor.create_context_entity.assert_called_once_with(project="project")

    run = Mock()
    crud_processor.read_context_entity.return_value = run
    assert processor.get_run("run-key") is run
    crud_processor.read_context_entity.assert_called_once_with("run-key")

    deleted = {"deleted": True}
    crud_processor.delete_context_entity.return_value = deleted
    assert processor.delete_run("run-key") is deleted
    crud_processor.delete_context_entity.assert_called_once_with("run-key")
