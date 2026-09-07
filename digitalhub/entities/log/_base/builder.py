# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._commons.enums import EntityKinds, EntityTypes
from digitalhub.entities._base.entity.builder import EntityBuilder
from digitalhub.entities.log._base.entity import Log
from digitalhub.entities.log._base.spec import LogSpec, LogValidator
from digitalhub.entities.log._base.status import LogStatus


class LogLogBuilder(EntityBuilder):
    """
    LogLogBuilder builder.
    """

    ENTITY_TYPE = EntityTypes.LOG.value
    ENTITY_CLASS = Log
    ENTITY_SPEC_CLASS = LogSpec
    ENTITY_SPEC_VALIDATOR = LogValidator
    ENTITY_STATUS_CLASS = LogStatus
    ENTITY_KIND = EntityKinds.LOG_LOG.value

    def build(
        self,
        project: str,
        kind: str,
        uuid: str,
        run: str,
        description: str | None = None,
        labels: list[str] | None = None,
        extensions: list | None = None,
        **kwargs,
    ) -> Log:
        """
        Create a new object.

        Parameters
        ----------
        project : str
            Project name.
        kind : str
            Kind of the log entity.
        uuid : str
            ID of the object.
        run : str
            Run ID associated with the log.
        description : str | None
            Description of the object (human readable).
        labels : list[str] | None
            List of labels.
        extensions : list | None
            List of extensions.
        **kwargs : dict
            Spec keyword arguments.

        Returns
        -------
        Log
            Object instance.
        """
        uuid = self.build_uuid(uuid)
        metadata = self.build_metadata(
            project=project,
            description=description,
            labels=labels,
        )
        spec = self.build_spec(**kwargs)
        status = self.build_status()
        return self.build_entity(
            project=project,
            uuid=uuid,
            run=run,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
            extensions=extensions,
        )

    def from_dict(self, obj: dict) -> Log:
        """
        Create a new object from dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to create object from.

        Returns
        -------
        Log
            Object instance.
        """
        parsed_dict = self._parse_dict(obj)
        return self.build_entity(**parsed_dict)

    def _parse_dict(self, obj: dict) -> dict:
        """
        Get dictionary and parse it to a valid entity dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        project = obj.get("project")
        kind = obj.get("kind")
        uuid = self.build_uuid(obj.get("id"))
        run = obj.get("run")
        metadata = self.build_metadata(**obj.get("metadata", {}))
        spec = self.build_spec(**obj.get("spec", {}))
        status = self.build_status(**obj.get("status", {}))
        user = obj.get("user")
        extensions = obj.get("extensions")
        return {
            "project": project,
            "uuid": uuid,
            "kind": kind,
            "run": run,
            "metadata": metadata,
            "spec": spec,
            "status": status,
            "user": user,
            "extensions": extensions,
        }
