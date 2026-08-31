# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec, SpecValidator

SpecT = typing.TypeVar("SpecT", bound="Spec")


def build_spec(spec_cls: type[SpecT], spec_validator: type[SpecValidator], **kwargs) -> SpecT:
    """
    Build entity spec object. This method is used to build entity
    specifications and is used to validate the parameters passed
    to the constructor.

    Parameters
    ----------
    spec_cls : type[Spec]
        Spec class.
    spec_validator : type[SpecValidator]
        Spec validator class.
    **kwargs : dict
        Keyword arguments for the constructor.

    Returns
    -------
    SpecT
        Spec object.
    """
    kwargs = spec_validator(**kwargs).to_dict()
    return spec_cls(**kwargs)
