# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base._base.section import EntitySection


class Status(EntitySection):
    """
    Base Status class.
    The status class contains information about the state of an entity,
    for example, the state of a RUNNING run, and eventual error message.
    """

    state: str | None = None
    message: str | None = None
    transitions: list[dict] | None = None
    k8s: dict | None = None
