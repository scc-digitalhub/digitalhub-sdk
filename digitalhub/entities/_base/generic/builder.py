from __future__ import annotations

from digitalhub.entities._base.generic.spec import GenericSpec
from digitalhub.entities._base.generic.status import GenericStatus


class GenericBuilder:
    """Mixin that builds a pass-through generic spec."""

    def build_spec(self, **kwargs) -> GenericSpec:
        return GenericSpec(**kwargs)

    def build_status(self, **kwargs) -> GenericStatus:
        return GenericStatus(**kwargs)
