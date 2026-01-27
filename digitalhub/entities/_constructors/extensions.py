# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities._base.extensions.entity import Extension


def build_extension(extensions: list[dict] | None = None) -> list[Extension]:
    """
    Build a list of Extension objects from a list of dictionaries.

    Parameters
    ----------
    extensions : list[dict]
        List of extension dictionaries.

    Returns
    -------
    list[Extension]
        List of Extension objects.
    """
    if extensions is None:
        return []
    return [Extension(**ext_dict) for ext_dict in extensions]
