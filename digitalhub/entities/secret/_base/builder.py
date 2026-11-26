# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._commons.enums import EntityTypes
from digitalhub.entities._mixin.versioned.builder import VersionedBuilder

if typing.TYPE_CHECKING:
    from digitalhub.entities.secret._base.entity import Secret


class SecretBuilder(VersionedBuilder):
    """
    Secret builder.
    """

    ENTITY_TYPE = EntityTypes.SECRET.value

    def build(self, kind: str, project: str, name: str, **kwargs) -> Secret:
        """
        Create a new secret, stored in Kubernetes under its name.

        Parameters
        ----------
        kind : str
            Kind the object.
        project : str
            Project name.
        name : str
            Object name.
        **kwargs : dict
            Other parameters of ``VersionedBuilder.build()``, then spec keyword arguments.

        Returns
        -------
        Secret
            Object instance.
        """
        return super().build(kind, project, name, path=f"secret://{name}", provider="kubernetes", **kwargs)
