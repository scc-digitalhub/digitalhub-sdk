# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.stores.client.common.config import get_client_config


class HttpElementsManager:
    """
    Manages HTTP headers and pagination for DHCore client requests.

    Provides utilities for setting and managing common HTTP headers
    like Content-Type for JSON requests.
    """

    @staticmethod
    def ensure_headers(**kwargs) -> dict:
        """
        Initialize headers dictionary in kwargs.

        Ensures parameter dictionary has 'headers' key for HTTP headers,
        guaranteeing consistent structure for all parameter building methods.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Dictionary with guaranteed 'headers' key containing
            empty dict if not already present.
        """
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        return kwargs

    @staticmethod
    def set_json_content_type(**kwargs) -> dict:
        """
        Set Content-Type header to application/json.

        Ensures that the 'Content-Type' header is set to 'application/json'
        for requests that require JSON payloads.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Dictionary with 'Content-Type' header set to 'application/json'.
        """
        kwargs = HttpElementsManager.ensure_headers(**kwargs)
        kwargs["headers"]["Content-Type"] = "application/json"
        return kwargs

    def set_pagination(self, partial: bool = False, **kwargs) -> dict:
        """
        Ensure pagination parameters are set in kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Pagination parameters set in 'params' of kwargs.
        """
        kwargs = self._ensure_params(**kwargs)

        if "page" not in kwargs["params"]:
            kwargs["params"]["page"] = get_client_config().default_page_start

        if partial:
            return kwargs

        if "size" not in kwargs["params"]:
            kwargs["params"]["size"] = get_client_config().default_page_size

        if "sort" not in kwargs["params"]:
            kwargs["params"]["sort"] = get_client_config().default_sort

        return kwargs

    @staticmethod
    def _ensure_params(**kwargs) -> dict:
        """
        Initialize parameter dictionary with query parameters structure.

        Ensures parameter dictionary has 'params' key for HTTP query parameters,
        guaranteeing consistent structure for all parameter building methods.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Parameters dictionary with guaranteed 'params' key containing
            empty dict if not already present.
        """
        if "params" not in kwargs:
            kwargs["params"] = {}
        return kwargs

    @staticmethod
    def read_page_number(**kwargs) -> int:
        """
        Read current page number from kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        int
            Current page number.
        """
        return kwargs["params"]["page"]

    @staticmethod
    def increment_page_number(**kwargs) -> dict:
        """
        Increment page number in kwargs.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to format. May be empty or contain various
            parameters for API operations.

        Returns
        -------
        dict
            Parameters dictionary with incremented 'page' number in 'params'.
        """
        kwargs["params"]["page"] += 1
        return kwargs
