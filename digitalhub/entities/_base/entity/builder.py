# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Callable

from digitalhub.entities._base.metadata.entity import Metadata
from digitalhub.entities._constructors.metadata import build_metadata
from digitalhub.entities._constructors.name import build_name
from digitalhub.entities._constructors.spec import build_spec
from digitalhub.entities._constructors.status import build_status
from digitalhub.entities._constructors.uuid import build_uuid
from digitalhub.utils.exceptions import BuilderError

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.entity import BaseEntity
    from digitalhub.entities._base.entity.spec import Spec
    from digitalhub.entities._base.entity.status import Status


class EntityBuilder(ABC):
    """
    Builder class for building entities.
    """

    # Class variables
    ENTITY_TYPE: str = None
    ENTITY_CLASS: type[BaseEntity] = None
    ENTITY_SPEC_CLASS: type[Spec] = None
    ENTITY_STATUS_CLASS: type[Status] = None
    ENTITY_KIND: str = None

    def __init__(self) -> None:
        if self.ENTITY_TYPE is None:
            raise BuilderError("ENTITY_TYPE must be set")
        if self.ENTITY_CLASS is None:
            raise BuilderError("ENTITY_CLASS must be set")
        if self.ENTITY_SPEC_CLASS is None:
            raise BuilderError("ENTITY_SPEC_CLASS must be set")
        if self.ENTITY_STATUS_CLASS is None:
            raise BuilderError("ENTITY_STATUS_CLASS must be set")
        if self.ENTITY_KIND is None:
            raise BuilderError("ENTITY_KIND must be set")

        validate_runtime_attributes: Callable[[], None] | None = getattr(self, "_validate_runtime_attributes", None)
        if validate_runtime_attributes is not None:
            validate_runtime_attributes()

    def build_name(self, name: str) -> str:
        """
        Build entity name.
        """
        return build_name(name)

    def build_uuid(self, uuid: str | None = None) -> str:
        """
        Build entity uuid.
        """
        return build_uuid(uuid)

    def build_metadata(self, **kwargs) -> Metadata:
        """
        Build entity metadata object.
        """
        return build_metadata(**kwargs)

    def build_spec(self, **kwargs) -> Spec:
        """
        Build entity spec object.
        """
        return build_spec(self.ENTITY_SPEC_CLASS, **kwargs)

    def build_status(self, **kwargs) -> Status:
        """
        Build entity status object.
        """
        return build_status(self.ENTITY_STATUS_CLASS, **kwargs)

    def build_entity(self, **kwargs) -> BaseEntity:
        """
        Build entity object.
        """
        return self.ENTITY_CLASS(**kwargs)

    @abstractmethod
    def build(self, *args, **kwargs) -> BaseEntity:
        """
        Build whole entity.
        """

    def from_dict(self, obj: dict) -> BaseEntity:
        """
        Build whole entity from dictionary.

        Parameters
        ----------
        obj : dict
            Dictionary to create object from.

        Returns
        -------
        BaseEntity
            Object instance. Top-level fields the entity does not know are
            kept and sent back by ``to_dict()``.
        """
        entity = self.build_entity(**self._parse_dict(obj))
        entity._extra = {key: value for key, value in obj.items() if key not in entity._obj_attr}
        return entity

    def _parse_dict(self, obj: dict) -> dict:
        """
        Parse the fields every entity has. Subclasses add their own
        fields to the result of ``super()._parse_dict(obj)``.

        The sections are read as they are: unlike ``build()``, reading adds
        no default and checks no value, so data written by a newer Core
        (a new state, for example) can still be read.

        Parameters
        ----------
        obj : dict
            Dictionary to parse.

        Returns
        -------
        dict
            Keyword arguments of the entity constructor.
        """
        return {
            "kind": obj.get("kind"),
            "metadata": Metadata.from_dict(obj.get("metadata", {})),
            "spec": self.ENTITY_SPEC_CLASS.from_dict(obj.get("spec", {})),
            "status": self.ENTITY_STATUS_CLASS.from_dict(obj.get("status", {})),
            "user": obj.get("user"),
        }

    def get_entity_type(self) -> str:
        """
        Get entity type.
        """
        return self.ENTITY_TYPE

    def get_kind(self) -> str:
        """
        Get entity kind.
        """
        return self.ENTITY_KIND
