from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec


class GenericSpec(Spec):
    """Spec that preserves arbitrary payload fields without filtering."""

    def __init__(self, **kwargs) -> None:
        self._any_setter(**kwargs)

    @classmethod
    def from_dict(cls, obj: dict) -> GenericSpec:
        return cls(**obj)
