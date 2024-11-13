from __future__ import annotations

import typing

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._operations.processor import processor

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.secret._base.spec import SecretSpec
    from digitalhub.entities.secret._base.status import SecretStatus


class Secret(VersionedEntity):
    """
    A class representing a secret.
    """

    ENTITY_TYPE = EntityTypes.SECRET.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: SecretSpec,
        status: SecretStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)
        self.spec: SecretSpec
        self.status: SecretStatus

    ##############################
    #  Secret methods
    ##############################

    def set_secret_value(self, value: str) -> None:
        """
        Update the secret value with a new one.

        Parameters
        ----------
        value : str
            Value of the secret.

        Returns
        -------
        None
        """
        obj = {self.name: value}
        processor.update_secret_data(self.project, self.ENTITY_TYPE, obj)

    def read_secret_value(self) -> dict:
        """
        Read the secret value from backend.

        Returns
        -------
        str
            Value of the secret.
        """
        params = {"keys": self.name}
        data = processor.read_secret_data(self.project, self.ENTITY_TYPE, params=params)
        return data[self.name]
