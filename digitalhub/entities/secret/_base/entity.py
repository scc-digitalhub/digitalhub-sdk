# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.context.entity import ContextEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.versioned.mixin import VersionedMixin
from digitalhub.entities._processors.processors import secret_processor

if typing.TYPE_CHECKING:
    from digitalhub.entities.secret._base.spec import SecretSpec
    from digitalhub.entities.secret._base.status import SecretStatus


class Secret(ContextEntity, VersionedMixin):
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
        metadata,
        spec,
        status,
        user: str | None = None,
    ) -> None:
        super().__init__(project, kind, metadata, spec, status, user)
        self._init_versioned_identity(project, name, uuid, kind)
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
        """
        obj = {self.name: value}
        secret_processor.update_secret_data(self.project, self.ENTITY_TYPE, obj)

    def read_secret_value(self) -> dict:
        """
        Read the secret value from backend.

        Returns
        -------
        str
            Value of the secret.
        """
        params = {"keys": self.name}
        data = secret_processor.read_secret_data(self.project, self.ENTITY_TYPE, params=params)
        return data[self.name]
