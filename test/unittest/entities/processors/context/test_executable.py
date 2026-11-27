# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import digitalhub.entities._processors.context.executable as executable_module
from digitalhub.entities._commons.enums import Relationship
from digitalhub.entities._mixin.source.entity import SourceEntityMixin
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities.run._base.processor import RunProcessor
from digitalhub.entities.task._base.processor import TaskProcessor
from digitalhub.utils.exceptions import EntityAlreadyExistsError, EntityError, EntityNotExistsError


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
    crud_processor.create_context_entity.side_effect = EntityAlreadyExistsError("exists")
    monkeypatch.setattr(
        executable_module.entity_factory,
        "get_task_kind_from_action",
        Mock(return_value="python+run"),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", Mock(return_value=task))

    with pytest.raises(EntityError, match="already exists"):
        processor.create_task(executable, "run")

    crud_processor.create_context_entity.assert_called_once_with(task)
    task.save.assert_not_called()


def test_update_task_replaces_the_task_through_the_crud_processor(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.kind = "python"
    executable._get_executable_string.return_value = "function-ref"
    processor.get_task = Mock(return_value=SimpleNamespace(id="task-id"))
    task = Mock(project="project", ENTITY_TYPE="task", id="task-id")
    build_entity = Mock(return_value=task)
    monkeypatch.setattr(executable_module.entity_factory, "get_task_kind_from_action", Mock(return_value="python+run"))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_params", build_entity)

    result = processor.update_task(executable, "run", labels=["x"])

    assert result is task
    build_entity.assert_called_once_with(
        labels=["x"], project="project", kind="python+run", function="function-ref", uuid="task-id"
    )
    crud_processor.update_context_entity.assert_called_once_with(task)
    task.update.assert_not_called()


def _task_dict(task_id: str = "task-id") -> dict:
    # Unknown kind: the generic task builder reads it, with or without runtimes.
    return {
        "project": "source-project",
        "id": task_id,
        "kind": "fake+job",
        "key": f"store://source-project/task/fake+job/{task_id}",
        "metadata": {"project": "source-project"},
        "spec": {"function": "fake://source-project/function:old-id"},
        "status": {},
    }


def _target_executable() -> Mock:
    executable = _executable()
    executable.project = "target-project"
    executable._get_executable_string.return_value = "fake://target-project/function:new-id"
    return executable


@pytest.mark.parametrize(("reset_id", "task_id"), [(False, "task-id"), (True, "new-task-id")])
def test_import_tasks_moves_tasks_to_the_executable(monkeypatch, reset_id: bool, task_id: str) -> None:
    # The tasks used to be created in the project of the file, pointing to
    # the executable of the file.
    crud_processor = Mock()
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-task-id"))

    ContextEntityExecutableProcessor(crud_processor).import_tasks(_target_executable(), [_task_dict()], reset_id)

    (task,) = crud_processor.create_context_entity.call_args.args
    saved = task.to_dict()
    assert task.ENTITY_TYPE == "task"
    assert saved["project"] == saved["metadata"]["project"] == "target-project"
    assert saved["id"] == task_id
    assert saved["key"] == f"store://target-project/task/fake+job/{task_id}"
    assert saved["spec"]["function"] == "fake://target-project/function:new-id"


def test_load_tasks_updates_existing_tasks_and_creates_missing_ones(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor.update_context_entity.side_effect = [None, EntityNotExistsError("missing")]

    ContextEntityExecutableProcessor(crud_processor).load_tasks(
        _target_executable(), [_task_dict("existing"), _task_dict("missing")]
    )

    updated = crud_processor.update_context_entity.call_args_list
    assert [c.args[0].id for c in updated] == ["existing", "missing"]
    (created,) = crud_processor.create_context_entity.call_args.args
    assert (created.project, created.id) == ("target-project", "missing")
    assert created.to_dict()["spec"]["function"] == "fake://target-project/function:new-id"


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
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    executable.key = "function-key"
    executable.kind = "python"
    task = Mock()
    run = Mock()
    run.extensions = [{"name": "task-extension"}]
    build_run = Mock(return_value=run)
    monkeypatch.setattr(TaskProcessor, "build_run", build_run)
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
    build_run.assert_called_once_with(task, "python+run", save=False, parameter="value")
    task.run.assert_not_called()
    assert run.extensions == [{"name": "task-extension"}, {"name": "run-extension"}]
    run.add_relationship.assert_called_once_with(Relationship.RUN_OF.value, "function-key")
    crud_processor.create_context_entity.assert_called_once_with(run)
    run.save.assert_not_called()


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


def test_execute_executable_creates_and_executes_run(monkeypatch) -> None:
    processor = ContextEntityExecutableProcessor(Mock())
    executable = _executable()
    run = Mock()
    executed = Mock()
    processor.create_run = Mock(return_value=run)
    execute = Mock(return_value=executed)
    monkeypatch.setattr(RunProcessor, "execute", execute)

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
    execute.assert_called_once_with(run, wait=True, log_info=False)


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
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
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
    crud_processor.create_context_entity.assert_called_once_with(trigger)
    trigger.save.assert_not_called()


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
    processor.import_tasks = Mock()
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
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True)

    assert result is executable
    assert executable.id == "new-id"
    assert executable.metadata.version == "new-id"
    crud_processor.create_context_entity.assert_called_once_with(executable)
    processor.import_tasks.assert_called_once_with(executable, [{"kind": "task", "status": {}}], reset_id=True)


def test_import_executable_updates_project_and_identity(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = VersionedExecutable()
    processor.import_tasks = Mock()
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
    monkeypatch.setattr(executable_module, "build_uuid", Mock(return_value="new-id"))
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    result = processor.import_executable_entity(file="entity.yaml", reset_id=True, context="target-project")

    assert result is executable
    assert executable.project == "target-project"
    assert executable.id == "new-id"
    assert executable.metadata.project == "target-project"
    assert executable.metadata.version == "new-id"
    assert executable.key == "store://target-project/function/function/function:new-id"
    crud_processor.create_context_entity.assert_called_once_with(executable)
    processor.import_tasks.assert_called_once_with(executable, [{"kind": "task", "status": {}}], reset_id=True)


def test_import_executable_converts_duplicate_error(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))
    crud_processor.create_context_entity.side_effect = EntityAlreadyExistsError("exists")

    with pytest.raises(EntityError, match="already exists"):
        processor.import_executable_entity(file="entity.yaml")


def test_load_executable_updates_existing_entity_and_loads_tasks(monkeypatch) -> None:
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    processor.load_tasks = Mock()
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
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    result = processor.load_executable_entity("entity.yaml")

    assert result is executable
    crud_processor.update_context_entity.assert_called_once_with(executable)
    crud_processor.create_context_entity.assert_not_called()
    processor.load_tasks.assert_called_once_with(executable, [{"kind": "task"}])


def test_load_executable_creates_missing_entity(monkeypatch) -> None:
    crud_processor = Mock()
    crud_processor.update_context_entity.side_effect = EntityNotExistsError("missing")
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = _executable()
    processor.load_tasks = Mock()
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    result = processor.load_executable_entity("entity.yaml")

    assert result is executable
    crud_processor.create_context_entity.assert_called_once_with(executable)
    processor.load_tasks.assert_called_once_with(executable, [])


class SourceExecutable(SourceEntityMixin, VersionedExecutable):
    """Executable with a source; records the project its source is checked in."""

    def __init__(self, events: list) -> None:
        super().__init__()
        self.events = events

    def _post_build_source_check(self):
        self.events.append(("source checked", self.project))
        return self


def test_import_executable_checks_local_source_in_the_target_project_before_saving(monkeypatch) -> None:
    # The check used to run inside from_dict(), before the identity update,
    # so a local source was uploaded under the project of the file.
    events: list = []
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = SourceExecutable(events)
    processor.import_tasks = Mock()
    crud_processor.create_context_entity.side_effect = lambda obj: events.append("saved")
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    processor.import_executable_entity(file="entity.yaml", context="target-project")

    assert events == [("source checked", "target-project"), "saved"]


def test_load_executable_checks_local_source_before_saving(monkeypatch) -> None:
    events: list = []
    crud_processor = Mock()
    processor = ContextEntityExecutableProcessor(crud_processor)
    executable = SourceExecutable(events)
    processor.load_tasks = Mock()
    crud_processor.update_context_entity.side_effect = lambda obj: events.append("saved")
    monkeypatch.setattr(
        executable_module,
        "read_yaml",
        Mock(return_value={"project": "project", "key": "store://project/function/function/function:entity-id"}),
    )
    monkeypatch.setattr(executable_module.entity_factory, "build_entity_from_dict", Mock(return_value=executable))

    processor.load_executable_entity("entity.yaml")

    assert events == [("source checked", "project"), "saved"]
