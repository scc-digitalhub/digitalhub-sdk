# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from requests import Response

from digitalhub.stores.client.http.errors import raise_for_response_error
from digitalhub.stores.client.http.response import parse_response_json
from digitalhub.utils.exceptions import (
    BackendError,
    BadRequestError,
    EntityAlreadyExistsError,
    EntityNotExistsError,
    ForbiddenError,
    MissingSpecError,
    UnauthorizedError,
)


def _response(status_code: int, body: str) -> Response:
    response = Response()
    response.status_code = status_code
    response.url = "https://example.test/resource"
    response.headers = {}
    response._content = body.encode()
    return response


@pytest.mark.parametrize(
    ("status_code", "body", "expected_error"),
    [
        (400, "Refresh token does not exist", BadRequestError),
        (400, "missing spec", MissingSpecError),
        (400, "Duplicated entity", EntityAlreadyExistsError),
        (401, "Unauthorized", UnauthorizedError),
        (403, "Forbidden", ForbiddenError),
        (404, "No such EntityName", EntityNotExistsError),
        (404, "resource missing", BackendError),
        (500, "backend failure", BackendError),
    ],
)
def test_raise_for_response_error_maps_backend_status_and_body(
    status_code: int,
    body: str,
    expected_error: type[BackendError],
) -> None:
    with pytest.raises(expected_error, match=body):
        raise_for_response_error(_response(status_code, body))


def test_parse_response_json_normalizes_invalid_json() -> None:
    response = _response(200, "not-json")

    with pytest.raises(BackendError, match="could not be parsed"):
        parse_response_json(response)
