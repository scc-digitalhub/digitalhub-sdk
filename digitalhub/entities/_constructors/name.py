# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import random
from enum import Enum

from pydantic import BaseModel, Field

from digitalhub.entities._constructors._resources import ADJECTIVE_REGISTRY, NAME_REGISTRY

NAME_REGEX = r"^[a-zA-Z0-9.+-_]+$"


class NameValidator(BaseModel):
    """
    Validate name format.
    """

    name: str = Field(min_length=1, max_length=256, pattern=NAME_REGEX)


def _random_enum_value(enum_cls: type[Enum]) -> str:
    """
    Get a random value from an Enum class.
    """
    return random.choice(list(enum_cls)).value


def build_name(name: str) -> str:
    """
    Build name.

    Parameters
    ----------
    name : str
        The name.

    Returns
    -------
    str
        The name.
    """
    NameValidator(name=name)
    return name


def random_name() -> str:
    """
    Generate a random name.

    Returns
    -------
    str
        The random name.
    """
    adjective = _random_enum_value(random.choice(ADJECTIVE_REGISTRY))
    noun = _random_enum_value(random.choice(NAME_REGISTRY))
    return f"{adjective}-{noun}"
