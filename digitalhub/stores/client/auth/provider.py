# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from typing import Protocol

if typing.TYPE_CHECKING:
    from digitalhub.stores.client.http.request import BackendReq


class AuthProvider(Protocol):
    """
    Authenticates the requests of one client.

    A client holds one provider: today the user's identity, later one per
    project. Providers do not own the HTTP transport, so clients with
    different providers share one connection pool.
    """

    def get_endpoint(self) -> str:
        """Return the DHCore endpoint that relative request paths are sent to."""

    def authenticate(self, backend_request: BackendReq) -> BackendReq:
        """Return an authenticated copy of a backend request."""

    def invalidate(self, rejected: BackendReq) -> bool:
        """
        Drop or refresh credentials the backend rejected.

        Parameters
        ----------
        rejected : BackendReq
            The request the backend rejected, as it was sent. A provider
            shared by threads uses it to tell whether another thread already
            replaced the credentials.

        Returns
        -------
        bool
            True if a retry with fresh credentials may succeed.
        """
