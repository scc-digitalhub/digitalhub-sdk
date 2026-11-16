# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Callable

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
    from digitalhub.entities._base.metadata.entity import Metadata


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

    @abstractmethod
    def from_dict(self, obj: dict) -> BaseEntity:
        """
        Build whole entity from dictionary.
        """

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
