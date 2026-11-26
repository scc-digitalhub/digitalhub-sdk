# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.factory.entity import entity_factory

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run
    from digitalhub.entities.task._base.entity import Task


class TaskProcessor:
    """Build the runs of a task."""

    def __init__(self, crud_processor: ContextEntityCRUDProcessor | None = None) -> None:
        self.crud_processor = ContextEntityCRUDProcessor() if crud_processor is None else crud_processor

    def build_run(
        self,
        task: Task,
        run_kind: str,
        save: bool = True,
        **kwargs,
    ) -> Run:
        """Build a run from a task, optionally persisting it."""
        exec_kind = entity_factory.get_executable_kind(task.kind)
        exec_type = entity_factory.get_entity_type_from_kind(exec_kind)
        kwargs[exec_type] = getattr(task.spec, exec_type)
        params = {
            **kwargs,
            "project": task.project,
            "task": task._get_task_string(),
            "kind": run_kind,
            "entity_type": EntityTypes.RUN.value,
        }
        if save:
            return self.crud_processor.create_context_entity_from_params(**params)
        return entity_factory.build_entity_from_params(**params)
