# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.entity.spec import Spec, SpecValidator


class ContainerimageSpec(Spec):
    """
    ImageSpec specifications.
    """

    def __init__(self, image: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.image = image


class ContainerimageValidator(SpecValidator):
    """
    ImageValidator validator.
    """

    image: str
    """Image URI."""
