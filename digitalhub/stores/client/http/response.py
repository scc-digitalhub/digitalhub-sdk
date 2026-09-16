# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from warnings import warn

from requests.exceptions import JSONDecodeError

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.http.errors import raise_for_response_error
from digitalhub.utils.exceptions import BackendError, ClientError

if TYPE_CHECKING:
    from requests import Response


def parse_response_json(response: Response) -> Any:
    """Parse a successful backend response and normalize invalid JSON."""
    try:
        return response.json()
    except JSONDecodeError:
        if response.text == "":
            return {}
        raise BackendError("Backend response could not be parsed.")


class ResponseProcessor:
    """
    Processes and validates HTTP responses from DHCore backend.

    Handles API version validation, error parsing, and response body parsing.
    Supports API versions {MIN_API_LEVEL} to {MAX_API_LEVEL}.
    """

    def process(self, response: Response) -> Any:
        """
        Process HTTP response with validation and parsing.
        """
        self._check_api_version(response)
        raise_for_response_error(response)
        return parse_response_json(response)

    def _check_api_version(self, response: Response) -> None:
        """
        Validate DHCore API version compatibility.
        """
        if "X-Api-Level" not in response.headers:
            return

        config = get_client_config()
        core_api_level = int(response.headers["X-Api-Level"])
        if not (config.min_api_level <= core_api_level <= config.max_api_level):
            raise ClientError("Backend API level not supported.")

        if config.lib_version < core_api_level:
            warn("Backend API level is higher than library version. Consider updating the package.")
