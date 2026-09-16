# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException
from requests.exceptions import Timeout as RequestsTimeout

from digitalhub.utils.exceptions import (
    BackendError,
    BadRequestError,
    EntityAlreadyExistsError,
    EntityNotExistsError,
    ForbiddenError,
    MissingSpecError,
    UnauthorizedError,
)

if TYPE_CHECKING:
    from requests import Response


def raise_for_transport_error(error: RequestException) -> NoReturn:
    """Normalize a requests transport exception to the SDK error contract."""
    if isinstance(error, RequestsTimeout):
        raise TimeoutError("Request to DHCore backend timed out.") from error
    if isinstance(error, RequestsConnectionError):
        raise ConnectionError("Unable to connect to DHCore backend.") from error
    raise BackendError(f"Some error occurred. {error}") from error


def raise_for_response_error(response: Response) -> None:
    """Raise the SDK error matching an unsuccessful backend response."""
    try:
        response.raise_for_status()
    except HTTPError as error:
        _raise_backend_error(response, error)
    except Exception as error:
        raise RuntimeError(f"Some error occurred: {error}") from error


def _raise_backend_error(response: Response, error: HTTPError) -> NoReturn:
    text = response.text
    msg_suffix = f"Response: {text}."

    if response.status_code == 400:
        if "missing spec" in text:
            raise MissingSpecError(f"Missing spec in backend. {msg_suffix}") from error
        if "Duplicated entity" in text:
            raise EntityAlreadyExistsError(f"Entity already exists. {msg_suffix}") from error
        raise BadRequestError(f"Bad request. {msg_suffix}") from error

    if response.status_code == 401:
        raise UnauthorizedError(f"Unauthorized. {msg_suffix}") from error

    if response.status_code == 403:
        raise ForbiddenError(f"Forbidden. {msg_suffix}") from error

    if response.status_code == 404:
        if "No such EntityName" in text:
            raise EntityNotExistsError(f"Entity does not exists. {msg_suffix}") from error
        raise BackendError(f"Not found. {msg_suffix}") from error

    raise BackendError(f"Backend error. {msg_suffix}") from error
