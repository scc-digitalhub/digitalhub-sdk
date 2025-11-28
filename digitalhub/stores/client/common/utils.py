# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.uri_utils import has_remote_scheme


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


def ensure_params(**kwargs) -> dict:
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


def add_param(key: str, value: Any | None, **kwargs) -> dict:
    """
    Add a single query parameter to kwargs.

    Parameters
    ----------
    key : str
        Parameter key.
    value : Any
        Parameter value.
    **kwargs : dict
        Keyword arguments to format. May be empty or contain various
        parameters for API operations.

    Returns
    -------
    dict
        Parameters dictionary with added key-value pair in 'params'.
    """
    kwargs["params"][key] = value
    return kwargs


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
    kwargs = ensure_headers(**kwargs)
    kwargs["headers"]["Content-Type"] = "application/json"
    return kwargs


def set_urlencoded_content_type(**kwargs) -> dict:
    """
    Set Content-Type header to application/x-www-form-urlencoded.

    Ensures that the 'Content-Type' header is set to
    'application/x-www-form-urlencoded' for requests that require
    form-encoded payloads.

    Parameters
    ----------
    **kwargs : dict
        Keyword arguments to format. May be empty or contain various
        parameters for API operations.

    Returns
    -------
    dict
        Dictionary with 'Content-Type' header set to
        'application/x-www-form-urlencoded'.
    """
    kwargs = ensure_headers(**kwargs)
    kwargs["headers"]["Content-Type"] = "application/x-www-form-urlencoded"
    return kwargs


def set_pagination(partial: bool = False, **kwargs) -> dict:
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
    kwargs = ensure_params(**kwargs)

    if "page" not in kwargs["params"]:
        kwargs["params"]["page"] = get_client_config().default_page_start

    if partial:
        return kwargs

    if "size" not in kwargs["params"]:
        kwargs["params"]["size"] = get_client_config().default_page_size

    if "sort" not in kwargs["params"]:
        kwargs["params"]["sort"] = get_client_config().default_sort

    return kwargs


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


def sanitize_endpoint(endpoint: str | None = None) -> str | None:
    """
    Validate and normalize endpoint URL.

    Ensures proper HTTP/HTTPS scheme, trims whitespace, and removes trailing slashes.

    Parameters
    ----------
    endpoint : str
        Endpoint URL to sanitize.

    Returns
    -------
    str or None
        Sanitized URL or None if input was None.

    Raises
    ------
    ClientError
        If endpoint lacks http:// or https:// scheme.
    """
    if endpoint is None:
        return
    if not has_remote_scheme(endpoint):
        raise ClientError("Invalid endpoint scheme. Must start with http:// or https://.")

    endpoint = endpoint.strip()
    return endpoint.removesuffix("/")
