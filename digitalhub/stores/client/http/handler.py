# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing

from digitalhub.stores.client.http.response import ResponseProcessor
from digitalhub.stores.client.http.transport import request
from digitalhub.utils.exceptions import BackendError, UnauthorizedError

if typing.TYPE_CHECKING:
    from digitalhub.stores.client.auth.client_configurator import ClientConfigurator


class HttpRequestHandler:
    """
    Handles HTTP request execution for DHCore client.

    Encapsulates all HTTP communication logic including request execution,
    automatic token refresh on authentication failures, and response processing.
    Works in coordination with configurator for authentication and response
    processor for parsing.
    """

    def __init__(self, configurator: ClientConfigurator) -> None:
        self._configurator = configurator
        self._response_processor = ResponseProcessor()

    def execute_request(self, method: str, api: str, **kwargs) -> dict:
        """
        Execute API call with full URL construction and authentication.

        Parameters
        ----------
        method : str
            HTTP method type (GET, POST, PUT, DELETE, etc.).
        api : str
            API endpoint path to call.
        **kwargs : dict
            Additional HTTP request arguments.

        Returns
        -------
        dict
            Response from the API call.
        """
        full_kwargs = self._configurator.get_auth_parameters(kwargs)
        url = f"{self._configurator.get_endpoint()}{api}"
        return self._execute_request(method, url, **full_kwargs)

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        retry_on_unauthorized: bool = True,
        **kwargs,
    ) -> dict:
        """
        Execute HTTP request with automatic handling.

        Sends HTTP request with authentication, handles token refresh on 401 errors,
        validates API version compatibility, and parses response. Uses 60-second
        timeout by default.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, PUT, DELETE, etc.).
        url : str
            Complete URL to request.
        retry_on_unauthorized : bool
            Whether credentials may be refreshed after an unauthorized response.
        **kwargs : dict
            Additional HTTP request arguments (headers, params, data, etc.).

        Returns
        -------
        dict
            Parsed response body as dictionary.
        """
        response = request(method, url, **kwargs)

        try:
            return self._response_processor.process(response)
        except UnauthorizedError:
            if retry_on_unauthorized and self._configurator.evaluate_refresh():
                kwargs = self._configurator.get_auth_parameters(kwargs)
                return self._execute_request(method, url, retry_on_unauthorized=False, **kwargs)
            raise
        except BackendError:
            raise
