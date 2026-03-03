# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import abstractmethod

from digitalhub.entities._base._base.entity import Base

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status
    from digitalhub.entities._base.metadata.entity import Metadata


class Entity(Base):
    """
    Abstract class for entities.

    An entity is a collection of metadata, specifications.and status
    representing a variety of objects handled by Digitalhub.
    """

    # Entity type
    # Need to be set in subclasses
    ENTITY_TYPE: str

    # Attributes to render as dict. Need to be expanded in subclasses.
    _obj_attr = ["kind", "metadata", "spec", "status", "user", "key"]

    def __init__(
        self,
        kind: str,
        metadata: Metadata,
        spec: Spec,
        status: Status,
        user: str | None = None,
    ) -> None:
        self.kind = kind
        self.metadata = metadata
        self.spec = spec
        self.status = status
        self.user = user

        # Need to be set in subclasses
        self.key: str

    @abstractmethod
    def save(self, update: bool = False) -> Entity:
        """
        Abstract save method.
        """

    @abstractmethod
    def refresh(self) -> Entity:
        """
        Abstract refresh method.
        """

    def _update_attributes(self, obj: Entity) -> None:
        """
        Update attributes.

        Parameters
        ----------
        obj : Entity
            The entity object to update attributes from.
        """
        self.metadata = obj.metadata
        self.spec = obj.spec
        self.status = obj.status
        self.user = obj.user

    @abstractmethod
    def export(self) -> str:
        """
        Abstract export method.
        """

    def set_name(self, value: str) -> None:
        """
        Set name in entity metadata. It overwrites the existing name if already set.

        Parameters
        ----------
        value : str
            The name value.
        """
        if not isinstance(value, str):
            raise ValueError("Name must be a string.")
        self.metadata.name = value

    def set_version(self, value: str) -> None:
        """
        Set version in entity metadata. It overwrites the existing version if already set.

        Parameters
        ----------
        value : str
            The version value.
        """
        if not isinstance(value, str):
            raise ValueError("Version must be a string.")
        self.metadata.version = value

    def set_description(self, value: str) -> None:
        """
        Set description in entity metadata. It overwrites the existing description if already set.

        Parameters
        ----------
        value : str
            The description value.
        """
        if not isinstance(value, str):
            raise ValueError("Description must be a string.")
        self.metadata.description = value

    def add_relationship(self, relation: str, dest: str, source: str | None = None) -> None:
        """
        Add relationship to entity metadata.

        Parameters
        ----------
        relation : str
            The type of relationship.
        dest : str
            The target entity.
        source : str
            The source entity.
        """
        if self.metadata.relationships is None:
            self.metadata.relationships = []
        obj = {"type": relation, "dest": dest}
        if source is not None:
            obj["source"] = source
        self.metadata.relationships.append(obj)

    def add_labels(self, values: list[str]) -> None:
        """
        Add multiple labels to entity metadata. If a label already exists, it is not added again.

        Parameters
        ----------
        values : list[str]
            The list of label values.
        """
        for value in values:
            self.add_label(value)

    def add_label(self, value: str) -> None:
        """
        Add a label to entity metadata. If the label already exists, it is not added again.

        Parameters
        ----------
        value : str
            The label value.
        """
        if not isinstance(value, str):
            raise ValueError(f"Label must be a string. Got {type(value)} instead.")
        if self.metadata.labels is None:
            self.metadata.labels = []
        if value not in self.metadata.labels:
            self.metadata.labels.append(value)

    def to_dict(self) -> dict:
        """
        Override default to_dict method to add the possibility to exclude
        some attributes. This requires to set a list of _obj_attr
        attributes in the subclass.

        Returns
        -------
        dict
            A dictionary containing the attributes of the entity instance.
        """
        return {k: v for k, v in super().to_dict().items() if k in self._obj_attr}

    def _post_create_hook_before_save(self) -> None:
        """
        Hook method called after the creation of the entity but before saving
        in Core.
        Can be overridden in subclasses to implement custom behavior.
        """

    def _post_read_hook(self) -> None:
        """
        Hook method called after reading the entity from Core.
        Can be overridden in subclasses to implement custom behavior.
        """

    def __repr__(self) -> str:
        """
        Return string representation of the entity object.

        Returns
        -------
        str
            A string representing the entity instance.
        """
        return str(self.to_dict())
