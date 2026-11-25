# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Protocol


class StoreCredentials(Protocol):
    """
    Credentials and configuration a store connects with.

    Stores receive them when built instead of reading a global client, so
    the owner of the store decides whose credentials it uses.
    """

    def get(self) -> dict[str, Any]:
        """Return the current credentials and configuration."""

    def refresh(self) -> bool:
        """
        Refresh credentials the storage rejected.

        Returns
        -------
        bool
            True if a retry with fresh credentials may succeed.
        """
