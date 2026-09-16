# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import replace
from typing import Any

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.stores.client.http.request import BERequest
from digitalhub.utils.exceptions import ClientError
from digitalhub.utils.uri_utils import has_remote_scheme


def with_headers(request: BERequest, **headers: str) -> BERequest:
    """Return a request with the supplied headers merged into its headers."""
    return replace(request, headers={**request.headers, **headers})


def with_data(request: BERequest, data: Any) -> BERequest:
    """Return a request with its payload replaced."""
    return replace(request, data=data)


def with_bearer_token(request: BERequest, token: str) -> BERequest:
    """Return a request with a bearer token header added."""
    return with_headers(request, Authorization=f"Bearer {token}")


def with_basic_auth(request: BERequest, user: str, password: str) -> BERequest:
    """Return a request with basic authentication options added."""
    return replace(request, options={**request.options, "auth": (user, password)})


def with_json_content_type(request: BERequest) -> BERequest:
    """Return a request with an application/json content type."""
    return with_headers(request, **{"Content-Type": "application/json"})


def with_urlencoded_content_type(request: BERequest) -> BERequest:
    """Return a request with a form-urlencoded content type."""
    return with_headers(request, **{"Content-Type": "application/x-www-form-urlencoded"})


def with_pagination(request: BERequest, partial: bool = False) -> BERequest:
    """Return a request with default pagination parameters filled in."""
    params = dict(request.params)
    params.setdefault("page", get_client_config().default_page_start)
    if not partial:
        params.setdefault("size", get_client_config().default_page_size)
        params.setdefault("sort", get_client_config().default_sort)
    return replace(request, params=params)


def next_page(request: BERequest) -> BERequest:
    """Return a request targeting the next page."""
    return replace(request, params={**request.params, "page": request.params["page"] + 1})


def sanitize_endpoint(endpoint: str | None = None) -> str | None:
    """
    Validate and normalize endpoint URL.
    """
    if endpoint is None:
        return
    endpoint = endpoint.strip()
    if not has_remote_scheme(endpoint):
        raise ClientError("Invalid endpoint scheme. Must start with http:// or https://.")

    return endpoint.removesuffix("/")
