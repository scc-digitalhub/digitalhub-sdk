# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing
from warnings import warn

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, JSONDecodeError, RequestException
from requests.exceptions import Timeout as RequestsTimeout

from digitalhub.stores.client.common.config import get_client_config
from digitalhub.utils.exceptions import (
    BackendError,
    BadRequestError,
    ClientError,
    EntityAlreadyExistsError,
    EntityNotExistsError,
    ForbiddenError,
    MissingSpecError,
    UnauthorizedError,
)

if typing.TYPE_CHECKING:
    from requests import Response


class ResponseProcessor:
    """
    Processes and validates HTTP responses from DHCore backend.

    Handles API version validation, error parsing, and response body parsing
    to dictionary. Supports API versions {MIN_API_LEVEL} to {MAX_API_LEVEL}.
    """

    min_api_level: int = get_client_config().min_api_level
    max_api_level: int = get_client_config().max_api_level
    lib_version: int = get_client_config().lib_version

    def process(self, response: Response) -> dict:
        """
        Process HTTP response with validation and parsing.

        Performs API version compatibility check, error parsing for failed
        responses, and JSON deserialization.

        Parameters
        ----------
        response : Response
            HTTP response object from backend.

        Returns
        -------
        dict
            Parsed response body as dictionary.
        """
        self._check_api_version(response)
        self._parse_error(response)
        return self._parse_json(response)

    def _check_api_version(self, response: Response) -> None:
        """
        Validate DHCore API version compatibility.

        Checks backend API version against supported range and warns if backend
        version is newer than library. Supported: {MIN_API_LEVEL} to {MAX_API_LEVEL}.

        Parameters
        ----------
        response : Response
            HTTP response containing X-Api-Level header.
        """
        if "X-Api-Level" not in response.headers:
            return

        core_api_level = int(response.headers["X-Api-Level"])
        if not (self.min_api_level <= core_api_level <= self.max_api_level):
            raise ClientError("Backend API level not supported.")

        if self.lib_version < core_api_level:
            warn("Backend API level is higher than library version. You should consider updating the library.")

    @staticmethod
    def _parse_json(response: Response) -> dict:
        """
        Parse HTTP response body to dictionary.

        Converts JSON response to Python dictionary, treating empty responses
        as valid and returning empty dict.

        Parameters
        ----------
        response : Response
            HTTP response object to parse.

        Returns
        -------
        dict
            Parsed response body as dictionary, or empty dict if body is empty.
        """
        try:
            return response.json()
        except JSONDecodeError:
            if response.text == "":
                return {}
            raise BackendError("Backend response could not be parsed.")

    def _parse_error(self, response: Response) -> None:
        """
        Handle DHCore API errors.

        Parses the HTTP response and raises appropriate exceptions based on
        the status code and response content. Maps backend errors to specific
        exception types for better error handling in the client code.

        Parameters
        ----------
        response : Response
            The HTTP response object from requests.

        Raises
        ------
        TimeoutError
            If the request timed out.
        ConnectionError
            If unable to connect to the backend.
        MissingSpecError
            If the backend reports a missing spec (400 status).
        EntityAlreadyExistsError
            If the entity already exists (400 status with specific message).
        BadRequestError
            For other 400 status codes.
        UnauthorizedError
            For 401 status codes.
        ForbiddenError
            For 403 status codes.
        EntityNotExistsError
            For 404 status codes with specific message.
        BackendError
            For other 404 status codes and general backend errors.
        RuntimeError
            For unexpected exceptions.
        """
        try:
            response.raise_for_status()

        except HTTPError as e:
            self._handle_http_error(response, e)

        except RequestsTimeout as e:
            raise TimeoutError("Request to DHCore backend timed out.") from e

        except RequestsConnectionError as e:
            raise ConnectionError("Unable to connect to DHCore backend.") from e

        except RequestException as e:
            raise BackendError(f"Some error occurred. {e}") from e

        except Exception as e:
            raise RuntimeError(f"Some error occurred: {e}") from e

    @staticmethod
    def _handle_http_error(response: Response, error: HTTPError) -> None:
        """
        Handle HTTP errors.

        Parameters
        ----------
        response : Response
            The HTTP response object.
        error : HTTPError
            The HTTP error exception.
        """
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
