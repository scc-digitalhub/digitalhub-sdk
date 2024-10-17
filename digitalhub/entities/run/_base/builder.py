from __future__ import annotations

import typing

from digitalhub.entities._base.unversioned.builder import UnversionedBuilder
from digitalhub.entities.utils.entity_types import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.run._base.entity import Run


class RunBuilder(UnversionedBuilder):
    """
    Run builder.
    """

    ENTITY_TYPE = EntityTypes.RUN.value

    def build(
        self,
        project: str,
        kind: str,
        uuid: str | None = None,
        labels: list[str] | None = None,
        task: str | None = None,
        local_execution: bool = False,
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
            ID of the object (UUID4, e.g. 40f25c4b-d26b-4221-b048-9527aff291e2).
        labels : list[str]
            List of labels.
        task : str
            Name of the task associated with the run.
        local_execution : bool
            Flag to determine if object has local execution.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Run
            Object instance.
        """
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=uuid,
            labels=labels,
        )
        spec = self.build_spec(
            task=task,
            local_execution=local_execution,
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            project=project,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )
