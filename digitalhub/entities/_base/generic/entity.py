from __future__ import annotations

from digitalhub.entities._base._base.entity import Base


class GenericEntity(Base):
    """Mixin for entities that need to keep arbitrary runtime fields."""

    def _set_generic_attributes(self, **kwargs) -> None:
        self._any_setter(**kwargs)
