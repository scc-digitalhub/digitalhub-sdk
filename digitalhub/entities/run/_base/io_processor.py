# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol, cast

from digitalhub.entities._commons.enums import Relationship
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities.run._base.entity import Run


class _InputsSpec(Protocol):
    """Spec of a run that takes inputs."""

    inputs: dict | None


def _inputs(run: Run) -> dict:
    """Keys of the run inputs, by parameter."""
    # Declared by the spec of the runs that take inputs.
    return getattr(run.spec, "inputs", None) or {}


def _outputs(run: Run) -> dict:
    """Keys of the run outputs, by name."""
    # Declared by the status of the runs that log outputs.
    return getattr(run.status, "outputs", None) or {}


class RunIOProcessor:
    """Inputs and outputs of the runs that reference entities by key."""

    def __init__(self, crud_processor: ContextEntityCRUDProcessor | None = None) -> None:
        self.crud_processor = ContextEntityCRUDProcessor() if crud_processor is None else crud_processor

    def inputs(self, run: Run, as_dict: bool = False) -> dict:
        """Read the entities of the run inputs, by parameter."""
        return {parameter: self._read(key, as_dict) for parameter, key in _inputs(run).items()}

    def outputs(self, run: Run, as_key: bool = False, as_dict: bool = False) -> dict:
        """Read the entities of the run outputs, by name; with ``as_key``, return the keys without reading."""
        if as_key:
            return dict(_outputs(run))
        return {name: self._read(key, as_dict) for name, key in _outputs(run).items()}

    def output(
        self,
        run: Run,
        output_name: str,
        as_key: bool = False,
        as_dict: bool = False,
    ) -> ContextEntity | dict | str | None:
        """Read the entity of one run output; with ``as_key``, return its key without reading."""
        key = _outputs(run).get(output_name)
        if key is None or as_key:
            return key
        return self._read(key, as_dict)

    def prepare_inputs(self, run: Run) -> None:
        """
        Prepare the inputs of a run about to execute.

        A local run consumes its inputs, and the runtime receives them as
        dictionaries in ``spec.inputs``.
        """
        self.crud_processor.refresh_context_entity(run)
        inputs = self.inputs(run, as_dict=True)
        if run.local_execution():
            for entity in inputs.values():
                run.add_relationship(relation=Relationship.CONSUMES.value, dest=entity.get("key"))
            self.crud_processor.update_context_entity(run)
        cast(_InputsSpec, run.spec).inputs = inputs

    def _read(self, key: str, as_dict: bool) -> ContextEntity | dict:
        """Read an entity by key, of whatever type the key says."""
        entity = self.crud_processor.read_context_entity(key)
        return entity.to_dict() if as_dict else entity
