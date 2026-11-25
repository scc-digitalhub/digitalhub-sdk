# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import ClassVar

from digitalhub.entities._commons.enums import EntityKinds
from digitalhub.entities._mixin.runtime_entity.builder import KindAction, RuntimeEntityBuilder
from digitalhub.entities.containerimage._base.builder import ContainerimageBuilder
from digitalhub.entities.containerimage._base.spec import ContainerimageSpec
from digitalhub.entities.containerimage._base.status import ContainerimageStatus
from digitalhub.entities.containerimage.containerimage.entity import ContainerimageContainerimage
from digitalhub.entities.dataitem._base.builder import DataitemBuilder
from digitalhub.entities.dataitem._base.status import DataitemStatus
from digitalhub.entities.dataitem.table.entity import DataitemTable
from digitalhub.entities.dataitem.table.spec import DataitemSpecTable
from digitalhub.factory.registry import registry
from digitalhub.plugins import (
    Action,
    BuilderDef,
    CrudPlugin,
    ExecFamily,
    Function,
    FunctionBuilder,
    Run,
    RunBuilder,
    RunSpecFunction,
    RunStatus,
    SourceBuilderMixin,
    Spec,
    Status,
    Task,
    TaskBuilder,
    TaskSpecFunction,
)


def _table() -> BuilderDef:
    return BuilderDef(
        EntityKinds.DATAITEM_TABLE, DataitemTable, DataitemSpecTable, DataitemStatus, base=DataitemBuilder
    )


class FakeKinds(Enum):
    FUNCTION = "fake"
    TASK_JOB = "fake+job"
    RUN_JOB = "fake+job:run"
    TASK_BUILD = "fake+build"
    RUN_BUILD = "fake+build:run"


class FakeActions(Enum):
    JOB = "job"
    BUILD = "build"


def new_function_fake() -> None:
    """Shortcut of the fake family."""


def _action(task: FakeKinds, run: FakeKinds) -> Action:
    return Action(
        task=BuilderDef(task, Task, TaskSpecFunction, Status, base=TaskBuilder),
        run=BuilderDef(run, Run, RunSpecFunction, RunStatus, base=RunBuilder),
    )


def _fake_family() -> ExecFamily:
    return ExecFamily(
        executable=BuilderDef(
            FakeKinds.FUNCTION,
            Function,
            Spec,
            Status,
            base=FunctionBuilder,
            mixins=(SourceBuilderMixin,),
            shortcuts=(CrudPlugin(new_function_fake),),
        ),
        actions={
            FakeActions.JOB: _action(FakeKinds.TASK_JOB, FakeKinds.RUN_JOB),
            FakeActions.BUILD: _action(FakeKinds.TASK_BUILD, FakeKinds.RUN_BUILD),
        },
        runtime_builder="fake_runtime.runtimes:Builder",
    )


def test_builder_def_generates_a_builder_with_its_classes() -> None:
    builder = _table().plugin().builder

    assert builder.__name__ == "DataitemTableBuilder"
    assert builder.__module__ == "digitalhub.factory.builders"
    assert builder.__bases__ == (DataitemBuilder,)
    assert builder.ENTITY_TYPE == "dataitem"
    assert builder.ENTITY_KIND == "table"
    assert builder.ENTITY_CLASS is DataitemTable
    assert builder.ENTITY_SPEC_CLASS is DataitemSpecTable
    assert builder.ENTITY_STATUS_CLASS is DataitemStatus


def test_builder_name_comes_from_entity_type_and_kind() -> None:
    definition = BuilderDef(
        EntityKinds.CONTAINERIMAGE_CONTAINERIMAGE,
        ContainerimageContainerimage,
        ContainerimageSpec,
        ContainerimageStatus,
        base=ContainerimageBuilder,
    )

    # The entity name alone would clash with the type builder, ContainerimageBuilder.
    assert definition.plugin().builder.__name__ == "ContainerimageContainerImageBuilder"


def test_generated_builder_builds_entities() -> None:
    builder = _table().plugin().builder()

    table = builder.build(project="project", name="table", kind="table", path="s3://bucket/table.parquet")

    assert isinstance(table, DataitemTable)
    assert isinstance(table.spec, DataitemSpecTable)
    assert isinstance(table.status, DataitemStatus)


def test_core_kinds_are_registered_through_generated_builders() -> None:
    builder = registry.get_entity_builder(EntityKinds.DATAITEM_TABLE.value)

    assert type(builder).__module__ == "digitalhub.factory.builders"
    assert builder.ENTITY_CLASS is DataitemTable


def test_exec_family_plugins_are_the_executable_then_task_and_run_of_each_action() -> None:
    plugins = _fake_family().plugins()

    assert [plugin.kind for plugin in plugins] == ["fake", "fake+job", "fake+job:run", "fake+build", "fake+build:run"]
    assert {plugin.runtime_builder for plugin in plugins} == {"fake_runtime.runtimes:Builder"}
    assert [shortcut.name for shortcut in plugins[0].shortcuts] == ["new_function_fake"]
    assert all(plugin.shortcuts == () for plugin in plugins[1:])


def test_exec_family_builders_share_one_topology() -> None:
    executable, task, run, *_ = (plugin.builder for plugin in _fake_family().plugins())
    topology = executable.__bases__[-1]

    assert topology.__name__ == "RuntimeEntityBuilderFake"
    assert topology.__module__ == executable.__module__ == "digitalhub.factory.builders"
    assert executable.__bases__ == (SourceBuilderMixin, FunctionBuilder, topology)
    assert task.__bases__ == (TaskBuilder, topology)
    assert run.__name__ == "RunFakeJobRunBuilder"
    assert run.__bases__ == (RunBuilder, topology)


def test_exec_family_topology_matches_a_handwritten_one() -> None:
    class Handwritten(RuntimeEntityBuilder):
        EXECUTABLE_KIND = "fake"
        TASKS_KINDS: ClassVar[list[KindAction]] = [KindAction("fake+job", "job"), KindAction("fake+build", "build")]
        RUN_KINDS: ClassVar[list[KindAction]] = [
            KindAction("fake+job:run", "job"),
            KindAction("fake+build:run", "build"),
        ]

    expected = Handwritten()
    generated = _fake_family().plugins()[0].builder()

    assert generated.get_executable_kind() == expected.get_executable_kind()
    assert generated.get_all_kinds() == expected.get_all_kinds()
    assert generated.get_all_actions() == expected.get_all_actions()
    for action in expected.get_all_actions():
        assert generated.get_task_kind_from_action(action) == expected.get_task_kind_from_action(action)
        assert generated.get_run_kind_from_action(action) == expected.get_run_kind_from_action(action)
        task_kind = expected.get_task_kind_from_action(action)
        assert generated.get_action_from_task_kind(task_kind) == action


def test_action_runtime_builder_replaces_the_family_one_for_its_task_and_run() -> None:
    family = _fake_family()
    actions = dict(family.actions)
    actions[FakeActions.BUILD] = Action(
        task=actions[FakeActions.BUILD].task,
        run=actions[FakeActions.BUILD].run,
        runtime_builder="fake_runtime.runtimes:BuildBuilder",
    )
    plugins = ExecFamily(family.executable, actions, family.runtime_builder).plugins()

    assert {plugin.kind: plugin.runtime_builder for plugin in plugins} == {
        "fake": "fake_runtime.runtimes:Builder",
        "fake+job": "fake_runtime.runtimes:Builder",
        "fake+job:run": "fake_runtime.runtimes:Builder",
        "fake+build": "fake_runtime.runtimes:BuildBuilder",
        "fake+build:run": "fake_runtime.runtimes:BuildBuilder",
    }
