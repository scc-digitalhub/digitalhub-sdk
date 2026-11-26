# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._base.entity.entity import BaseEntity
from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.utils.generic_utils import decode_base64_string

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities.log._base.spec import LogSpec


class Log(BaseEntity):
    """
    A class representing a log.
    """

    ENTITY_TYPE = EntityTypes.LOG.value
    _obj_attr = ("kind", "metadata", "spec", "status", "user", "project", "id", "run", "extensions")

    def __init__(
        self,
        project: str,
        uuid: str,
        kind: str,
        metadata: dict,
        spec: LogSpec,
        status: Status,
        run: str,
        user: str | None = None,
        extensions: list | None = None,
    ) -> None:
        super().__init__(kind, metadata, spec, status, user)

        self.spec: LogSpec
        self.status: Status

        self.project = project
        self.id = uuid
        self.extensions = extensions
        self.run = run

        self._content: str | None = None
        self._text: str | None = None

    ##############################
    #  Log methods
    ##############################

    def set_content(self, content: str | None) -> None:
        """
        Set log content.

        Parameters
        ----------
        content : str | None
            Log content.
        """
        self._content = content
        self._text = decode_base64_string(content) if content is not None else None

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
