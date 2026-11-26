# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.runtime_entity.builder import EntityError, RuntimeEntityBuilder
from digitalhub.entities._mixin.unversioned.builder import UnversionedBuilder

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class RunBuilder(UnversionedBuilder, RuntimeEntityBuilder):
    """
    Run builder.
    """

    ENTITY_TYPE = EntityTypes.RUN.value

    def build(
        self,
        project: str,
        kind: str,
        name: str | None = None,
        uuid: str | None = None,
        extensions: list[dict] | None = None,
        labels: list[str] | None = None,
        task: str | None = None,
        **kwargs,
    ) -> Run:
        """
        Create a new object.

        Parameters
        ----------
        project : str
            Project name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        name : str
            Name stored in entity metadata.
        labels : list[str]
            List of labels.
        task : str
            Name of the task associated with the run.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Run
            Object instance.
        """
        if self.VALIDATE_RUNTIME_ATTRIBUTES:
            if task is None:
                raise EntityError("Missing task in run spec")
            self._check_kind_validity(task)

        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=name,
            labels=labels,
        )
        if name is None:
            name = metadata.name
        spec = self.build_spec(task=task, **kwargs)
        status = self.build_status()
        return self.build_entity(
            project=project,
            name=name,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
            extensions=extensions,
        )

    def _check_kind_validity(self, task: str) -> None:
        """
        Check kind validity.

        Parameters
        ----------
        task : str
            Task string.
        """
        task_kind = task.split("://")[0]
        if task_kind not in self.get_all_kinds():
            raise EntityError(f"Invalid run '{self.ENTITY_KIND}' for task kind '{task_kind}'")

    def _parse_dict(self, obj: dict) -> dict:
        """
        Add the name, taken from the metadata when missing, and the
        extensions to the unversioned fields.

        Parameters
        ----------
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            Keyword arguments of the entity constructor.
        """
        name = obj.get("name")
        if name is None:
            name = obj.get("metadata", {}).get("name")
        return {**super()._parse_dict(obj), "name": name, "extensions": obj.get("extensions", [])}
