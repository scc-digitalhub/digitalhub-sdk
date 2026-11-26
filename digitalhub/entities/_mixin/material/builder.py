# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.entities._mixin.versioned.builder import VersionedBuilder
from digitalhub.utils.exceptions import EntityError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.context.entity import ContextEntity
    from digitalhub.entities._mixin.material.protocol import MaterialProtocol


class MaterialBuilder(VersionedBuilder):
    """
    Builder of the material entities: artifact, dataitem and model.
    """

    def build(
        self,
        kind: str,
        project: str,
        name: str,
        *,
        path: str | None = None,
        extensions: list[dict] | None = None,
        **kwargs,
    ) -> ContextEntity:
        """
        Create a new object.

        Parameters
        ----------
        kind : str
            Kind the object.
        project : str
            Project name.
        name : str
            Object name.
        path : str
            Object path on local file system or remote storage. It is also the destination path of upload() method.
        extensions : list[dict]
            List of extension dictionaries.
        **kwargs : dict
            Other parameters of ``VersionedBuilder.build()``, then spec keyword arguments.

        Returns
        -------
        ContextEntity
            Object instance.
        """
        if path is None:
            raise EntityError("Path must be provided.")
        entity = super().build(kind, project, name, path=path, **kwargs)
        if extensions is not None:
            typing.cast("MaterialProtocol", entity).extensions.extend(extensions)
        return entity

    def _parse_dict(self, obj: dict) -> dict:
        """
        Add the extensions to the versioned fields.

        Parameters
        ----------
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            Keyword arguments of the entity constructor.
        """
        return {**super()._parse_dict(obj), "extensions": obj.get("extensions", [])}
