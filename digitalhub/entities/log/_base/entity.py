# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.versioned.entity import VersionedEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.utils.generic_utils import decode_base64_string

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.metadata import Metadata
    from digitalhub.entities.log._base.spec import LogSpec
    from digitalhub.entities.log._base.status import LogStatus


class Log(VersionedEntity):
    """
    A class representing a log.
    """

    ENTITY_TYPE = EntityTypes.LOG.value

    def __init__(
        self,
        project: str,
        name: str,
        uuid: str,
        kind: str,
        metadata: Metadata,
        spec: LogSpec,
        status: LogStatus,
        user: str | None = None,
    ) -> None:
        super().__init__(project, name, uuid, kind, metadata, spec, status, user)
        self.spec: LogSpec
        self.status: LogStatus
        self._content: str | None = None
        self._text: str | None = None

    ##############################
    #  Log methods
    ##############################

    def set_content(self, content: str) -> None:
        """
        Set log content.

        Parameters
        ----------
        content : str
            Log content.
        """
        self._content = content
        self._text = decode_base64_string(content)

    @property
    def text(self) -> str | None:
        """
        Get log content as text.

        Returns
        -------
        str | None
            Log content as text.
        """
        return self._text
