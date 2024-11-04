from __future__ import annotations

import typing

from digitalhub.entities._base.runtime_entity.builder import RuntimeEntityBuilder
from digitalhub.entities._base.versioned.builder import VersionedBuilder
from digitalhub.entities._commons.enums import EntityTypes

if typing.TYPE_CHECKING:
    from digitalhub.entities.workflow._base.entity import Workflow


class WorkflowBuilder(VersionedBuilder, RuntimeEntityBuilder):
    """
    Workflow builder.
    """

    ENTITY_TYPE = EntityTypes.WORKFLOW.value

    def build(
        self,
        kind: str,
        project: str,
        name: str,
        uuid: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        embedded: bool = False,
        **kwargs,
    ) -> Workflow:
        """
        Create a new object.

        Parameters
        ----------
        project : str
            Project name.
        name : str
            Object name.
        kind : str
            Kind the object.
        uuid : str
            ID of the object.
        description : str
            Description of the object (human readable).
        labels : list[str]
            List of labels.
        embedded : bool
            Flag to determine if object spec must be embedded in project spec.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Workflow
            Object instance.
        """
        name = self.build_name(name)
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            name=name,
            description=description,
            labels=labels,
            embedded=embedded,
        )
        spec = self.build_spec(
            **kwargs,
        )
        status = self.build_status()
        return self.build_entity(
            project=project,
            name=name,
            uuid=uuid,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )
