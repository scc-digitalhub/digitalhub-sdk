# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from digitalhub.entities._base.entity.spec import Spec, SpecValidator


def build_spec(spec_cls: Spec, spec_validator: SpecValidator, **kwargs) -> Spec:
    """
    Build entity spec object. This method is used to build entity
    specifications and is used to validate the parameters passed
    to the constructor.

    Parameters
    ----------
    spec_cls : Spec
        Spec class.
    spec_validator : SpecValidator
        Spec validator class.
    **kwargs : dict
        Keyword arguments for the constructor.

    Returns
    -------
    Spec
        Spec object.
    """
    kwargs = spec_validator(**kwargs).to_dict()
    return spec_cls(**kwargs)
