# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from threading import current_thread
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import digitalhub.entities._processors.context.executable as executable_module
from digitalhub.entities._commons.enums import Relationship, State
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities.log._base.entity import Log
from digitalhub.entities.run._base.spec import RunSpec
from digitalhub.stores.client.common.enums import ApiType, BackendOp
from digitalhub.stores.client.compiler.operation import ClientOp
from digitalhub.stores.client.compiler.options import LogsOptions
from digitalhub.stores.client.compiler.targets import ContextEntityTarget
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError
from digitalhub.utils.generic_utils import encode_string


def _context(name: str = "project") -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _executable() -> Mock:
    executable = Mock()
    executable.ENTITY_TYPE = "function"
    executable.name = "function"
    executable.project = "project"
    executable.to_dict.return_value = {"kind": "function"}
    return executable


def test_task_operations_use_backend_without_entity_cache(monkeypatch) -> None:
    crud_processor = Mock()
    existing_task = SimpleNamespace(id="task-id", key="task-key")
    crud_processor.list_context_entities.return_value = [existing_task]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )

    assert processor.get_task(executable, "run") is existing_task
    assert "_tasks" not in executable.__dict__

    crud_processor.list_context_entities.assert_called_once_with(
        project="project",
        entity_type="task",
        function="function-ref",
        kind="python+run",
    )


def test_get_task_reads_fresh_backend_state_on_every_call(monkeypatch) -> None:
    crud_processor = Mock()
    first = SimpleNamespace(id="task-1", key="task-key-1")
    second = SimpleNamespace(id="task-2", key="task-key-2")
    crud_processor.list_context_entities.side_effect = [[first], [second]]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )

    assert processor.get_task(executable, "run") is first
    assert processor.get_task(executable, "run") is second
    assert crud_processor.list_context_entities.call_count == 2


def test_create_task_rechecks_backend_and_handles_duplicate(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor.list_context_entities.side_effect = [[], []]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    task = Mock()
    task.save.side_effect = EntityAlreadyExistsError("exists")
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", Mock(return_value=task))

    with pytest.raises(EntityError, match="already exists"):
        processor.create_task(executable, "run")


def test_import_tasks_does_not_store_tasks_on_executable(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    task = SimpleNamespace(
        spec=SimpleNamespace(function="function-ref"),
        kind="python+run",
        save=Mock(),
    )
    monkeypatch.setattr(
        executable_module.entity_factory,
        "build_entity_from_dict",
        Mock(return_value=task),
    )

    processor.import_tasks(executable, [{"kind": "python+run"}])

    task.save.assert_called_once_with()
    assert "_tasks" not in executable.__dict__


def test_list_executable_runs_applies_relationship_filter() -> None:
    crud_processor = Mock()
    crud_processor.list_context_entities.return_value = ["run"]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable._get_executable_string.return_value = "function-key"

    result = processor.list_executable_runs(executable, state="RUNNING")

    assert result == ["run"]
    crud_processor.list_context_entities.assert_called_once_with(
        project="project",
        entity_type="run",
        state="RUNNING",
        function="function-key",
    )


def test_get_executable_run_matches_id_or_key() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    first = SimpleNamespace(id="run-id", key="run-key")
    processor.list_executable_runs = Mock(return_value=[first])

    assert processor.get_executable_run(executable, "run-id") is first
    assert processor.get_executable_run(executable, "run-key") is first

    with pytest.raises(EntityError, match="does not belong"):
        processor.get_executable_run(executable, "missing")


def test_create_run_applies_relationship_and_extensions(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    executable.key = "function-key"
    executable.kind = "python"
    task = Mock()
    run = Mock()
    run.extensions = [{"name": "task-extension"}]
    task.run.return_value = run
    processor.get_or_create_task = Mock(return_value=task)
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_run_kind_from_action",
        Mock(return_value="python+run"),
    )

    result = processor.create_run(
        executable,
        "execute",
        extensions=[{"name": "run-extension"}],
        parameter="value",
    )

    assert result is run
    processor.get_or_create_task.assert_called_once_with(executable, "execute")
    task.run.assert_called_once_with("python+run", save=False, parameter="value")
    assert run.extensions == [{"name": "task-extension"}, {"name": "run-extension"}]
    run.add_relationship.assert_called_once_with(Relationship.RUN_OF.value, "function-key")
    run.save.assert_called_once_with()


def test_delete_executable_run_checks_relationship_before_deleting() -> None:
    crud_processor = Mock()
    crud_processor.delete_context_entity.return_value = {"deleted": True}
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    run = SimpleNamespace(key="run-key")
    processor.get_executable_run = Mock(return_value=run)

    result = processor.delete_executable_run(executable, "run-id")

    assert result == {"deleted": True}
    processor.get_executable_run.assert_called_once_with(executable, "run-id")
    crud_processor.delete_context_entity.assert_called_once_with(
        "run-key",
        entity_type="run",
        unversioned=True,
    )


def test_execute_executable_creates_and_executes_run() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    run = Mock()
    executed = Mock()
    processor.create_run = Mock(return_value=run)
    processor.execute_run = Mock(return_value=executed)

    result = processor.execute_executable(
        executable,
        "execute",
        wait=True,
        log_info=False,
        extensions=[{"name": "extension"}],
        parameter="value",
    )

    assert result is executed
    processor.create_run.assert_called_once_with(
        executable,
        "execute",
        extensions=[{"name": "extension"}],
        parameter="value",
    )
    processor.execute_run.assert_called_once_with(run, wait=True, log_info=False)


def test_execute_run_builds_and_runs_local_run_in_caller_thread() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = Mock()
    run.local_execution.return_value = True
    processor.build_run = Mock()
    processor.run_run = Mock(side_effect=lambda _run: current_thread())
    processor.wait_run = Mock()

    result = processor.execute_run(run, wait=True)

    assert result is current_thread()
    processor.build_run.assert_called_once_with(run)
    processor.run_run.assert_called_once_with(run)
    processor.wait_run.assert_not_called()


def test_execute_run_returns_backend_run_without_waiting() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = Mock()
    run.local_execution.return_value = False
    processor.build_run = Mock()
    processor.run_run = Mock()
    processor.wait_run = Mock()

    assert processor.execute_run(run) is run

    processor.build_run.assert_not_called()
    processor.run_run.assert_not_called()
    processor.wait_run.assert_not_called()


def test_execute_run_waits_for_backend_run_when_requested() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = Mock()
    run.local_execution.return_value = False
    waited_run = Mock()
    processor.wait_run = Mock(return_value=waited_run)

    assert processor.execute_run(run, wait=True, log_info=False) is waited_run

    processor.wait_run.assert_called_once_with(run, log_info=False)


def test_build_task_run_adds_executable_reference(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    task = SimpleNamespace(
        kind="python+job",
        project="project",
        spec=SimpleNamespace(function="function-ref"),
        _get_task_string=Mock(return_value="task-ref"),
    )
    run = Mock()
    monkeypatch.setattr(executable_module.entity_factory, "get_executable_kind", Mock(return_value="python-function"))
    monkeypatch.setattr(executable_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="function"))
    build_entity = Mock(return_value=run)
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", build_entity)

    result = processor.build_task_run(task, "python+run", save=False, labels=["run"])

    assert result is run
    build_entity.assert_called_once_with(
        project="project",
        task="task-ref",
        kind="python+run",
        entity_type="run",
        function="function-ref",
        labels=["run"],
    )


def test_get_run_executable_reads_reference_through_crud(monkeypatch) -> None:
    executable = Mock()
    executable.to_dict.return_value = {"kind": "python-function"}
    crud_processor = Mock()
    crud_processor.read_context_entity.return_value = executable
    processor = ContextEntityExecutableProcessor(crud_processor)
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_executable_kind",
        Mock(return_value="python-function"),
    )
    monkeypatch.setattr(executable_module.entity_factory, "get_entity_type_from_kind", Mock(return_value="function"))
    run = SimpleNamespace(
        kind="python-run",
        project="project",
        spec=SimpleNamespace(function="python-function://project/model:version"),
    )

    result = processor.get_run_executable(run)

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
    processor = ContextEntityExecutableProcessor(crud_processor)
    run = SimpleNamespace(project="project", spec=SimpleNamespace(task="task://project/task-id"))

    result = processor.get_run_task(run)

    assert result == {"kind": "python-task"}
    crud_processor.read_unversioned_entity.assert_called_once_with(
        "task-id",
        entity_type="task",
        project="project",
    )


def test_build_run_preserves_fields_from_runtime_merge(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = SimpleNamespace(
        kind="python+run",
        project="project",
        spec=RunSpec(task="task://project/task-id"),
        status=SimpleNamespace(state=State.READY.value),
        to_dict=Mock(return_value={"spec": {"task": "task://project/task-id"}}),
        update=Mock(),
    )
    processor.get_run_executable = Mock(return_value={"spec": {"function": "function-ref"}})
    processor.get_run_task = Mock(return_value={"spec": {"instructions": ["build"]}})
    runtime = Mock()
    runtime.build.return_value = {
        "task": "task://project/task-id",
        "function": "function-ref",
        "future_backend_field": "preserved",
    }
    monkeypatch.setattr(
        executable_module.runtime_factory,
        "build_runtime",
        Mock(return_value=runtime),
    )

    processor.build_run(run)

    assert run.spec.future_backend_field == "preserved"
    assert run.status.state == State.BUILT.value
    run.update.assert_called_once_with()


def test_wait_run_returns_without_sleep_for_terminal_state(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value),
        refresh=Mock(side_effect=lambda: setattr(run.status, "state", State.COMPLETED.value)),
    )
    sleep = Mock()
    clock_values = iter([10.0, 10.25])
    monkeypatch.setattr(
        executable_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    assert processor.wait_run(run, log_info=False) is run

    run.refresh.assert_called_once_with()
    sleep.assert_not_called()


def test_wait_run_sleeps_only_between_polls_and_times_out(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value),
        refresh=Mock(),
    )
    sleep = Mock()
    clock_values = iter([0.0, 0.0, 1.0, 2.0])
    monkeypatch.setattr(
        executable_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    with pytest.raises(TimeoutError, match="Run run-id did not finish within 2s"):
        processor.wait_run(run, log_info=False, timeout=2, poll_interval=1)

    assert run.refresh.call_count == 3
    assert sleep.call_args_list == [call(1), call(1)]


def test_wait_run_limits_sleep_to_remaining_timeout(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = SimpleNamespace(
        id="run-id",
        status=SimpleNamespace(state=State.RUNNING.value),
        refresh=Mock(),
    )
    sleep = Mock()
    clock_values = iter([0.0, 0.0, 1.0, 1.5])
    monkeypatch.setattr(
        executable_module,
        "time",
        SimpleNamespace(monotonic=lambda: next(clock_values), sleep=sleep),
    )

    with pytest.raises(TimeoutError):
        processor.wait_run(run, log_info=False, timeout=1.5, poll_interval=1)

    assert sleep.call_args_list == [call(1), call(0.5)]


@pytest.mark.parametrize(
    ("timeout", "poll_interval"),
    [(-1, 1), (None, 0)],
)
def test_wait_run_rejects_invalid_timing_values(timeout, poll_interval) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    run = SimpleNamespace(refresh=Mock())

    with pytest.raises(ValueError):
        processor.wait_run(run, timeout=timeout, poll_interval=poll_interval)

    run.refresh.assert_not_called()


def test_run_run_ends_execution_when_setup_fails() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    processor.start_run_execution = Mock()
    processor.end_run_execution = Mock()
    run = SimpleNamespace(
        refresh=Mock(),
        _setup_execution=Mock(side_effect=RuntimeError("setup failed")),
    )

    with pytest.raises(RuntimeError, match="setup failed"):
        processor.run_run(run)

    processor.end_run_execution.assert_called_once_with(run)


def test_start_run_execution_validates_state_before_registration() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    context = Mock()
    run = SimpleNamespace(
        status=SimpleNamespace(state=State.CREATED.value),
        local_execution=Mock(return_value=True),
        update=Mock(),
        _context=Mock(return_value=context),
    )

    with pytest.raises(EntityError, match="not in a state to run"):
        processor.start_run_execution(run)

    context.set_run.assert_not_called()


def test_start_run_execution_rolls_back_registration() -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    context = Mock()
    run = SimpleNamespace(
        status=SimpleNamespace(state=State.BUILT.value),
        local_execution=Mock(return_value=True),
        update=Mock(side_effect=RuntimeError("update failed")),
        _context=Mock(return_value=context),
    )

    with pytest.raises(RuntimeError, match="update failed"):
        processor.start_run_execution(run)

    context.set_run.assert_called_once_with(run)
    context.unset_run.assert_called_once_with()


@pytest.mark.parametrize(
    ("local_execution", "expected_state"),
    [
        (False, "BACKEND"),
        (True, "RUNTIME"),
    ],
)
def test_run_run_state_precedence(monkeypatch, local_execution: bool, expected_state: str) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    processor.start_run_execution = Mock()
    processor.end_run_execution = Mock()
    run = SimpleNamespace(
        kind="python+run",
        project="project",
        status=SimpleNamespace(to_dict=Mock(return_value={"state": "BACKEND"})),
        refresh=Mock(),
        _setup_execution=Mock(),
        local_execution=Mock(return_value=local_execution),
        to_dict=Mock(return_value={}),
        update=Mock(),
    )
    runtime = Mock()
    runtime.run.return_value = {"state": "RUNTIME"}
    build_status = Mock(return_value=SimpleNamespace(state=expected_state))
    monkeypatch.setattr(
        executable_module.runtime_factory,
        "build_runtime",
        Mock(return_value=runtime),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_status", build_status)

    result = processor.run_run(run)

    assert result is run
    build_status.assert_called_once_with("python+run", state=expected_state)
    assert run.status.state == expected_state


def test_read_run_logs_builds_logs_and_decodes_content(monkeypatch) -> None:
    client = Mock()
    context = SimpleNamespace(client=client)
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
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=context))
    run = SimpleNamespace(project="project", ENTITY_TYPE="run", id="run-id")

    result = ContextEntityExecutableProcessor(Mock()).read_run_logs(run, state="READY")

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


def test_list_and_get_executable_trigger() -> None:
    crud_processor = Mock()
    trigger = SimpleNamespace(id="trigger-id", key="trigger-key")
    crud_processor.list_context_entities.return_value = [trigger]
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable._get_executable_string.return_value = "function-ref"

    assert processor.list_executable_triggers(executable, state="READY") == [trigger]
    assert processor.get_executable_trigger(executable, "trigger-key") is trigger
    crud_processor.list_context_entities.assert_any_call(
        project="project",
        entity_type="trigger",
        state="READY",
        function="function-ref",
    )


def test_create_trigger_builds_spec_without_mutating_template(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    task = Mock()
    task._get_task_string.return_value = "task-ref"
    processor.get_or_create_task = Mock(return_value=task)
    spec = Mock()
    spec.to_dict.return_value = {"validated": True}
    build_spec = Mock(return_value=spec)
    trigger = Mock()
    build_entity = Mock(return_value=trigger)
    monkeypatch.setattr(executable_module.entity_factory, "get_run_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(executable_module.entity_factory, "build_spec", build_spec)
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", build_entity)
    template = {"custom": "value"}

    result = processor.create_trigger(
        executable,
        "execute",
        "lifecycle",
        "on-demand",
        template=template,
        description="A trigger",
    )

    assert result is trigger
    assert template == {"custom": "value"}
    build_spec.assert_called_once_with(
        "python+run",
        custom="value",
        task="task-ref",
        function="function-ref",
    )
    build_entity.assert_called_once_with(
        description="A trigger",
        project="project",
        kind="lifecycle",
        name="on-demand",
        function="function-ref",
        task="task-ref",
        template={"validated": True},
    )
    trigger.save.assert_called_once_with()


class VersionedExecutable(VersionedMixin):
    ENTITY_TYPE = "function"

    def __init__(self, project: str = "project", entity_id: str = "entity-id") -> None:
        self.project = project
        self.kind = "function"
        self.metadata = SimpleNamespace(project=project, version=entity_id)
        self._init_versioned_identity(project, "function", entity_id, self.kind)
        self.import_tasks = Mock()

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "kind": self.kind,
            "name": self.name,
            "id": self.id,
            "key": self.key,
            "metadata": {
                "project": self.metadata.project,
                "version": self.metadata.version,
            },
        }


def test_import_executable_rejects_missing_or_ambiguous_source() -> None:
    processor = ContextEntityExecutableProcessor(Mock())

    with pytest.raises(ValueError, match="Provide key or file"):
        processor.import_executable_entity()

    with pytest.raises(ValueError, match="Provide key or file"):
        processor.import_executable_entity(file="entity.yaml", key="entity-key")


def test_import_executable_reads_file_resets_id_and_imports_tasks(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    processor.import_tasks = Mock()
    build_entity = Mock(side_effect=[executable, imported])
    create_entity = Mock(return_value={"kind": "function", "id": "new-id"})
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(
            return_value=[
                {"project": "project", "key": "store://project/function/function/function:entity-id"},
                {"kind": "task"},
            ]
        ),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))
    crud_processor._create_context_entity = create_entity

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True)

    assert result is imported
    assert executable.id == "new-id"
    assert executable.metadata.version == "new-id"
    create_entity.assert_called_once_with(_context(), "function", executable.to_dict.return_value)
    processor.import_tasks.assert_called_once_with(imported, [{"kind": "task", "status": {}}])


def test_import_executable_updates_project_and_identity(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = VersionedExecutable()
    imported = VersionedExecutable(project="target-project", entity_id="new-id")
    processor.import_tasks = Mock()
    context = _context("target-project")
    response = imported.to_dict()
    crud_processor._create_context_entity.return_value = response
    build_entity = Mock(side_effect=[executable, imported])
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(
            return_value=[
                {"project": "project", "key": "store://project/function/function/function:entity-id"},
                {"kind": "task"},
            ]
        ),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=context))
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True, context="target-project")

    assert result is imported
    assert executable.project == "target-project"
    assert executable.id == "new-id"
    assert executable.metadata.project == "target-project"
    assert executable.metadata.version == "new-id"
    assert executable.key == "store://target-project/function/function/function:new-id"
    crud_processor._create_context_entity.assert_called_once_with(context, "function", executable.to_dict())
    processor.import_tasks.assert_called_once_with(imported, [{"kind": "task", "status": {}}])


def test_import_executable_converts_duplicate_error(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))
    crud_processor._create_context_entity.side_effect = EntityAlreadyExistsError("exists")

    with pytest.raises(EntityError, match="already exists"):
        processor.import_executable_entity(file="entity.yaml")


def test_load_executable_updates_existing_entity_and_imports_tasks(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    processor.import_tasks = Mock()
    backend_response = {"project": "project", "kind": "function", "id": "backend-id"}
    crud_processor._update_context_entity.return_value = backend_response
    build_entity = Mock(side_effect=[executable, imported])
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(
            return_value=[
                {"project": "project", "key": "store://project/function/function/function:entity-id"},
                {"kind": "task"},
            ]
        ),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.load_executable_entity("entity.yaml")

    assert result is imported
    crud_processor._update_context_entity.assert_called_once_with(
        _context(),
        "function",
        executable.id,
        executable.to_dict.return_value,
    )
    crud_processor._create_context_entity.assert_not_called()
    assert build_entity.call_args_list[1] == call(backend_response, entity_type="function")
    processor.import_tasks.assert_called_once_with(imported, [{"kind": "task"}])


def test_load_executable_creates_missing_entity(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor._update_context_entity.side_effect = EntityNotExistsError("missing")
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    imported = _executable()
    processor.import_tasks = Mock()
    backend_response = {"project": "project", "kind": "function", "id": "backend-id"}
    crud_processor._create_context_entity.return_value = backend_response
    build_entity = Mock(side_effect=[executable, imported])
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module, "get_context", Mock(return_value=_context()))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", build_entity)

    result = processor.load_executable_entity("entity.yaml")

    assert result is imported
    crud_processor._create_context_entity.assert_called_once_with(
        _context(),
        "function",
        executable.to_dict.return_value,
    )
    assert build_entity.call_args_list[1] == call(backend_response, entity_type="function")
    processor.import_tasks.assert_called_once_with(imported, [])
