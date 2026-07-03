from __future__ import annotations

from digitalhub.entities._base.entity.status import Status


class GenericStatus(Status):
    """Status that preserves arbitrary payload fields without filtering."""

    def __init__(self, **kwargs) -> None:
        self._any_setter(**kwargs)
