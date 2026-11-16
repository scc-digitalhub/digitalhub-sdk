# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec

SpecT = typing.TypeVar("SpecT", bound="Spec")


def build_spec(
    spec_cls: type[SpecT],
    **kwargs,
) -> SpecT:
    """
    Build entity spec object. This method is used to build entity
    specifications and is used to validate the parameters passed
    to the constructor.

    Parameters
    ----------
    spec_cls : type[Spec]
        Spec class.
    **kwargs : dict
        Keyword arguments for the constructor.

    Returns
    -------
    SpecT
        Spec object.
    """
    if not spec_cls.ALLOW_EXTRA_INPUTS:
        allowed_fields = set(spec_cls.model_fields)
        allowed_fields.update(field.alias for field in spec_cls.model_fields.values() if isinstance(field.alias, str))
        unknown_fields = sorted(set(kwargs) - allowed_fields)
        if unknown_fields:
            names = ", ".join(unknown_fields)
            raise TypeError(f"Unexpected spec parameter(s) for {spec_cls.__name__}: {names}")

    return spec_cls(**kwargs)
